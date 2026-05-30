from __future__ import annotations

from datetime import datetime
from typing import Iterable

from supabase import create_client

from ..core.config import (
    REVIEW_QUEUE_TABLE,
    SUPABASE_KEY,
    SUPABASE_URL,
)
from ..models import AuditReport, AuditRequest, ReviewItem, ReviewUpdate


class ReviewQueueError(Exception):
    pass


def _ensure_supabase() -> None:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ReviewQueueError("Supabase is not configured for review queue.")


def _client():
    _ensure_supabase()
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def _compute_risk_score(report: AuditReport) -> float:
    if not report.issues:
        return 0.0
    weights = {"high": 1.0, "medium": 0.6, "low": 0.3}
    total = 0.0
    for issue in report.issues:
        total += weights.get(issue.severity, 0.5)
    return min(1.0, total / max(1, len(report.issues)))


def _average_confidence(report: AuditReport) -> float | None:
    values = [issue.confidence for issue in report.issues if issue.confidence is not None]
    if not values:
        return None
    return sum(values) / len(values)


def _serialize_issues(report: AuditReport) -> list[dict]:
    return [issue.model_dump() for issue in report.issues]


def enqueue_review(report: AuditReport, payload: AuditRequest, tenant_id: str | None) -> ReviewItem | None:
    try:
        client = _client()
        now = datetime.utcnow().isoformat()
        record = {
            "document_id": payload.document_id,
            "provider": payload.provider,
            "status": "pending",
            "summary": report.summary,
            "issues": _serialize_issues(report),
            "review_required": report.review_required,
            "review_reasons": report.review_reasons,
            "risk_score": _compute_risk_score(report),
            "confidence_avg": _average_confidence(report),
            "tenant_id": tenant_id,
            "created_at": now,
            "updated_at": now,
        }
        result = client.table(REVIEW_QUEUE_TABLE).insert(record).execute()
        if not result.data:
            return None
        return ReviewItem.model_validate(result.data[0])
    except Exception as exc:
        raise ReviewQueueError(str(exc)) from exc


def list_reviews(status: str | None, limit: int = 50) -> list[ReviewItem]:
    try:
        client = _client()
        query = client.table(REVIEW_QUEUE_TABLE).select("*").order("created_at", desc=True)
        if status:
            query = query.eq("status", status)
        query = query.limit(limit)
        result = query.execute()
        return [ReviewItem.model_validate(item) for item in (result.data or [])]
    except Exception as exc:
        raise ReviewQueueError(str(exc)) from exc


def get_review(review_id: str) -> ReviewItem | None:
    try:
        client = _client()
        result = (
            client.table(REVIEW_QUEUE_TABLE)
            .select("*")
            .eq("id", review_id)
            .limit(1)
            .execute()
        )
        if not result.data:
            return None
        return ReviewItem.model_validate(result.data[0])
    except Exception as exc:
        raise ReviewQueueError(str(exc)) from exc


def update_review(review_id: str, payload: ReviewUpdate) -> ReviewItem | None:
    try:
        client = _client()
        updates = payload.model_dump(exclude_none=True)
        if not updates:
            return get_review(review_id)
        updates["updated_at"] = datetime.utcnow().isoformat()
        result = (
            client.table(REVIEW_QUEUE_TABLE)
            .update(updates)
            .eq("id", review_id)
            .execute()
        )
        if not result.data:
            return None
        return ReviewItem.model_validate(result.data[0])
    except Exception as exc:
        raise ReviewQueueError(str(exc)) from exc


def review_queue_ready() -> bool:
    try:
        client = _client()
        response = client.table(REVIEW_QUEUE_TABLE).select("id").limit(1).execute()
        return response.data is not None
    except Exception:
        return False
