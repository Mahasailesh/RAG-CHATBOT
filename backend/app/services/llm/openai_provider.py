from __future__ import annotations

import json

from openai import OpenAI

from ...core.config import OPENAI_API_KEY, OPENAI_DEFAULT_MODEL, OPENAI_ORG_ID, OPENAI_PROJECT_ID
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


class OpenAIProvider:
    name = "openai"

    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or OPENAI_API_KEY

    def audit(
        self, payload: DocumentText, model: str | None, context: str | None
    ) -> AuditReport:
        client = OpenAI(
            api_key=self._api_key,
            organization=OPENAI_ORG_ID,
            project=OPENAI_PROJECT_ID,
        )
        response = client.chat.completions.create(
            model=model or OPENAI_DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_content(payload, context)},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
        content = response.choices[0].message.content or ""
        try:
            data = json.loads(content)
            return AuditReport.model_validate(data)
        except Exception as exc:
            raise ProviderResponseError("Provider returned invalid JSON.") from exc
