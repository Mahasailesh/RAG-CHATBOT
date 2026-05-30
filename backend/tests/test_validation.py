import pytest
from pydantic import ValidationError

from app.core.config import MAX_TEXT_CHARS
from app.models import AuditRequest


def test_pages_must_not_be_empty() -> None:
    with pytest.raises(ValidationError):
        AuditRequest(pages={}, provider="gemini")


def test_page_numbers_start_at_one() -> None:
    with pytest.raises(ValidationError):
        AuditRequest(pages={0: "Invalid page"}, provider="gemini")


def test_payload_size_limit() -> None:
    oversized = "x" * (MAX_TEXT_CHARS + 1)
    with pytest.raises(ValidationError):
        AuditRequest(pages={1: oversized}, provider="gemini")


def test_provider_must_be_allowed() -> None:
    with pytest.raises(ValidationError):
        AuditRequest(pages={1: "Content"}, provider="unknown")


def test_model_is_trimmed() -> None:
    payload = AuditRequest(pages={1: "Content"}, provider="gemini", model="  gemini-2.5-flash  ")
    assert payload.model == "gemini-2.5-flash"


def test_blank_model_becomes_none() -> None:
    payload = AuditRequest(pages={1: "Content"}, provider="gemini", model="   ")
    assert payload.model is None


def test_retrieval_k_bounds() -> None:
    with pytest.raises(ValidationError):
        AuditRequest(pages={1: "Content"}, provider="gemini", retrieval_k=0)
    with pytest.raises(ValidationError):
        AuditRequest(pages={1: "Content"}, provider="gemini", retrieval_k=50)
