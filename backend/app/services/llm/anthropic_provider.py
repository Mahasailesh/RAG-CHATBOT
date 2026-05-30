from __future__ import annotations

import json

from anthropic import Anthropic

from ...core.config import ANTHROPIC_API_KEY, ANTHROPIC_DEFAULT_MODEL
from ...models import AuditReport, DocumentText
from .errors import ProviderResponseError

SYSTEM_PROMPT = (
    "You are an immigration document auditor. Identify discrepancies in names, "
    "dates, financial figures, and other critical fields across pages. Use only "
    "the provided document text and the reference material supplied. If there is "
    "insufficient evidence, return no issues and note the uncertainty in summary. "
    "Populate issue fields with category, field, expected, found, page, severity, "
    "notes, source, evidence, and confidence (0-1). Set source to 'model'. Evidence should cite any "
    "reference material snippets used. Return a response that matches the provided response schema."
)


def _build_user_content(payload: DocumentText, context: str | None) -> str:
    lines: list[str] = []
    if payload.document_id:
        lines.append(f"Document ID: {payload.document_id}")
    for page_number in sorted(payload.pages.keys()):
        lines.append(f"[Page {page_number}]")
        lines.append(payload.pages[page_number])
    if context:
        lines.append("")
        lines.append("Reference material:")
        lines.append(context)
    return "\n".join(lines)


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or ANTHROPIC_API_KEY

    def audit(
        self, payload: DocumentText, model: str | None, context: str | None
    ) -> AuditReport:
        client = Anthropic(api_key=self._api_key)
        response = client.messages.create(
            model=model or ANTHROPIC_DEFAULT_MODEL,
            max_tokens=1200,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": _build_user_content(payload, context)}],
        )
        text = "".join(block.text for block in response.content if block.type == "text")
        try:
            data = json.loads(text)
            return AuditReport.model_validate(data)
        except Exception as exc:
            raise ProviderResponseError("Provider returned invalid JSON.") from exc
