from fastapi import APIRouter, HTTPException, Header, Request
import time

from ..models import AccuracyReport, AuditReport, AuditRequest, ReviewItem, ReviewUpdate
from ..core.config import (
    ACCURACY_REPORT_PATH,
    ENABLE_METRICS,
    ENABLE_REVIEW_QUEUE,
    ENABLE_TENANTS,
    RATE_LIMIT,
    REVIEW_ADMIN_TOKEN,
    TENANT_HEADER_ID,
    TENANT_HEADER_TOKEN,
)
from ..core.accuracy import load_accuracy_report
from ..core.limiter import limiter
from ..core.logging import log_audit_event
from ..core.metrics import record_audit, snapshot_metrics
from ..core.tenancy import load_tenant_policies, validate_tenant
from ..services.rag import run_rag_audit
from ..services.llm.errors import (
    ProviderAuthError,
    ProviderNotAllowed,
    ProviderResponseError,
)
from ..services.rag.errors import KnowledgeBaseError
from ..services.rag.knowledge_base import kb_ready
from ..services.review_queue import (
    ReviewQueueError,
    enqueue_review,
    get_review,
    list_reviews,
    review_queue_ready,
    update_review,
)

TENANT_POLICIES = load_tenant_policies()

router = APIRouter()


@router.get("/health")
def health_check() -> dict:
    return {
        "status": "ok",
        "kb_ready": kb_ready(),
        "review_queue_ready": review_queue_ready() if ENABLE_REVIEW_QUEUE else False,
    }


@router.get("/health/kb")
def kb_health_check() -> dict:
    return {"status": "ok" if kb_ready() else "missing"}


@router.get("/metrics")
def metrics() -> dict:
    if not ENABLE_METRICS:
        raise HTTPException(status_code=404, detail="Metrics not enabled.")
    return snapshot_metrics()


@router.get("/accuracy", response_model=AccuracyReport)
def accuracy_report() -> AccuracyReport:
    report = load_accuracy_report(ACCURACY_REPORT_PATH)
    if report is None:
        raise HTTPException(status_code=404, detail="Accuracy report not available.")
    return report


def _require_review_access(request: Request) -> None:
    if not ENABLE_REVIEW_QUEUE:
        raise HTTPException(status_code=404, detail="Review queue not enabled.")
    if REVIEW_ADMIN_TOKEN:
        token = request.headers.get("X-Review-Token")
        if token != REVIEW_ADMIN_TOKEN:
            raise HTTPException(status_code=401, detail="Invalid review token.")


@router.post("/audit", response_model=AuditReport)
@limiter.limit(RATE_LIMIT)
def audit_document(
    request: Request,
    payload: AuditRequest,
    x_provider_api_key: str | None = Header(default=None, alias="X-Provider-Api-Key"),
) -> AuditReport:
    try:
        tenant_id = request.headers.get(TENANT_HEADER_ID)
        tenant_token = request.headers.get(TENANT_HEADER_TOKEN)
        tenant_policy = None
        if ENABLE_TENANTS:
            tenant_policy = validate_tenant(tenant_id, tenant_token, TENANT_POLICIES)
            if tenant_policy is None:
                raise HTTPException(status_code=401, detail="Invalid tenant credentials.")

        start = time.perf_counter()
        report = run_rag_audit(
            payload,
            x_provider_api_key,
            allowed_providers=tenant_policy.allowed_providers if tenant_policy else None,
            allow_byok=tenant_policy.allow_byok if tenant_policy else None,
        )
        latency_ms = (time.perf_counter() - start) * 1000
        page_count = len(payload.pages)
        char_count = sum(len(text) for text in payload.pages.values())
        log_audit_event(
            provider=payload.provider,
            status=report.status,
            page_count=page_count,
            char_count=char_count,
            retrieval_k=payload.retrieval_k,
            latency_ms=latency_ms,
            tenant_id=tenant_id,
        )
        if ENABLE_METRICS:
            high_count = sum(1 for issue in report.issues if issue.severity == "high")
            record_audit(payload.provider, report.status, len(report.issues), report.review_required, high_count)
        if ENABLE_REVIEW_QUEUE and report.review_required:
            try:
                enqueue_review(report, payload, tenant_id)
            except ReviewQueueError:
                pass
        return report
    except ProviderNotAllowed as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except ProviderAuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    except ProviderResponseError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except KnowledgeBaseError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/review", response_model=list[ReviewItem])
def review_list(
    request: Request,
    status: str | None = None,
    limit: int = 50,
) -> list[ReviewItem]:
    _require_review_access(request)
    try:
        return list_reviews(status=status, limit=limit)
    except ReviewQueueError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/review/{review_id}", response_model=ReviewItem)
def review_detail(request: Request, review_id: str) -> ReviewItem:
    _require_review_access(request)
    try:
        item = get_review(review_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Review item not found.")
        return item
    except ReviewQueueError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.patch("/review/{review_id}", response_model=ReviewItem)
def review_update(request: Request, review_id: str, payload: ReviewUpdate) -> ReviewItem:
    _require_review_access(request)
    try:
        item = update_review(review_id, payload)
        if item is None:
            raise HTTPException(status_code=404, detail="Review item not found.")
        return item
    except ReviewQueueError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
