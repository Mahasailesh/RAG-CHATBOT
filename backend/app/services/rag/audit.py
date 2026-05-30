from __future__ import annotations

from ...models import AuditReport, AuditRequest
from ..llm.registry import get_provider
from ..rules import run_rule_checks
from .retrieval import format_context, retrieve_context


def run_rag_audit(
    payload: AuditRequest,
    byok_key: str | None,
    allowed_providers: list[str] | None = None,
    allow_byok: bool | None = None,
) -> AuditReport:
    provider = get_provider(
        payload.provider,
        byok_key,
        allowed_providers=allowed_providers,
        allow_byok=allow_byok,
    )
    rule_issues, rule_review_reasons = run_rule_checks(payload)
    chunks = retrieve_context(payload, payload.retrieval_k)
    context = format_context(chunks)
    report = provider.audit(payload, payload.model, context)
    combined_issues = rule_issues + report.issues
    for issue in combined_issues:
        if issue.source is None:
            issue.source = "model"
        if issue.confidence is None:
            if issue.source == "rule":
                issue.confidence = {
                    "high": 0.95,
                    "medium": 0.9,
                    "low": 0.85,
                }.get(issue.severity, 0.9)
            else:
                issue.confidence = {
                    "high": 0.75,
                    "medium": 0.6,
                    "low": 0.5,
                }.get(issue.severity, 0.6)
    normalized_status = "issues_found" if combined_issues else "ok"

    review_reasons = list(rule_review_reasons)
    if any(issue.severity == "high" for issue in combined_issues):
        review_reasons.append("High severity discrepancies detected.")
    review_required = bool(review_reasons)
    summary = report.summary or ""
    if rule_issues:
        suffix = f"Rule-based checks flagged {len(rule_issues)} item(s)."
        summary = f"{summary} {suffix}".strip()

    return report.model_copy(
        update={
            "status": normalized_status,
            "document_id": payload.document_id or report.document_id,
            "issues": combined_issues,
            "summary": summary or None,
            "review_required": review_required,
            "review_reasons": sorted(set(review_reasons)),
        }
    )
