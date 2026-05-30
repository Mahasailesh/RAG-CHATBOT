from __future__ import annotations

from typing import Protocol

from ...models import AuditReport, DocumentText


class LLMProvider(Protocol):
    name: str

    def audit(
        self, payload: DocumentText, model: str | None, context: str | None
    ) -> AuditReport:
        ...
