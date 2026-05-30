from ...models import AuditReport, AuditRequest
from .registry import get_provider


def run_audit(
    payload: AuditRequest, byok_key: str | None, context: str | None = None
) -> AuditReport:
    provider = get_provider(payload.provider, byok_key)
    report = provider.audit(payload, payload.model, context)
    normalized_status = "issues_found" if report.issues else "ok"
    return report.model_copy(
        update={
            "status": normalized_status,
            "document_id": payload.document_id or report.document_id,
        }
    )
