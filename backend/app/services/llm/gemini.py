from __future__ import annotations

import json

from google import genai
from google.genai import types

from ...core.config import GEMINI_DEFAULT_MODEL
from ...models import AuditReport, DocumentText
from .errors import ProviderResponseError

SYSTEM_INSTRUCTION = (
    "You are an immigration document auditor. Identify discrepancies in names, "
    "dates, financial figures, and other critical fields across pages. Use only "
    "the provided document text and the reference material supplied. If there is "
    "insufficient evidence, return no issues and note the uncertainty in summary. "
    "Populate issue fields with category, field, expected, found, page, severity, "
    "notes, source, evidence, and confidence (0-1). Set source to 'model'. Evidence should cite any "
    "reference material snippets used. Set status to 'issues_found' when any issues "
    "exist, otherwise 'ok'. Return a response that matches the provided response schema."
)


def _build_contents(payload: DocumentText, context: str | None) -> str:
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


def _extract_json(response) -> dict:
    parsed = getattr(response, "parsed", None)
    if parsed is not None:
        return parsed
    text = response.text or ""
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ProviderResponseError("Provider returned invalid JSON.") from exc


class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str):
        self._api_key = api_key

    def audit(self, payload: DocumentText, model: str | None, context: str | None) -> AuditReport:
        client = genai.Client(api_key=self._api_key)
        response = client.models.generate_content(
            model=model or GEMINI_DEFAULT_MODEL,
            contents=_build_contents(payload, context),
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=AuditReport,
                temperature=0,
            ),
        )
        data = _extract_json(response)
        try:
            return AuditReport.model_validate(data)
        except Exception as exc:
            raise ProviderResponseError("Provider returned invalid JSON.") from exc
