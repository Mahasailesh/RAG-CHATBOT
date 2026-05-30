from __future__ import annotations

import json

import httpx

from ...core.config import OLLAMA_BASE_URL, OLLAMA_DEFAULT_MODEL
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


class OllamaProvider:
    name = "ollama"

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        default_model: str | None = None,
    ):
        self._base_url = (base_url or OLLAMA_BASE_URL).rstrip("/")
        self._api_key = api_key
        self._default_model = default_model or OLLAMA_DEFAULT_MODEL

    def audit(
        self, payload: DocumentText, model: str | None, context: str | None
    ) -> AuditReport:
        request_body = {
            "model": model or self._default_model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_content(payload, context)},
            ],
            "format": "json",
            "stream": False,
        }
        headers = {}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        try:
            response = httpx.post(
                f"{self._base_url}/api/chat",
                json=request_body,
                headers=headers,
                timeout=60.0,
            )
        except httpx.HTTPError as exc:
            raise ProviderResponseError("Unable to reach Ollama.") from exc
        if response.status_code >= 400:
            raise ProviderResponseError("Ollama returned an error response.")
        data = response.json()
        content = data.get("message", {}).get("content", "")
        try:
            return AuditReport.model_validate(json.loads(content))
        except Exception as exc:
            raise ProviderResponseError("Provider returned invalid JSON.") from exc
