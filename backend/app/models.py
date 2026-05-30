from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .core.config import ALLOWED_PROVIDERS, DEFAULT_PROVIDER, MAX_TEXT_CHARS


class DocumentText(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: Optional[str] = Field(default=None, max_length=128)
    pages: Dict[int, str] = Field(
        ...,
        description="Page-number keyed text map extracted in the browser.",
    )

    @field_validator("pages")
    @classmethod
    def validate_pages(cls, value: Dict[int, str]) -> Dict[int, str]:
        if not value:
            raise ValueError("pages must not be empty")
        for page_number, text in value.items():
            if page_number < 1:
                raise ValueError("page numbers must start at 1")
            if not isinstance(text, str) or not text.strip():
                raise ValueError(f"page {page_number} text is empty")
        return value

    @model_validator(mode="after")
    def validate_total_size(self) -> "DocumentText":
        total_chars = sum(len(text) for text in self.pages.values())
        if total_chars > MAX_TEXT_CHARS:
            raise ValueError("payload exceeds maximum allowed size")
        return self


class AuditRequest(DocumentText):
    provider: str = Field(default=DEFAULT_PROVIDER, max_length=32)
    model: Optional[str] = Field(default=None, max_length=64)
    retrieval_k: Optional[int] = Field(default=None, ge=1, le=20)

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in ALLOWED_PROVIDERS:
            raise ValueError("provider is not enabled")
        return normalized

    @field_validator("model")
    @classmethod
    def normalize_model(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class Discrepancy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: Literal["name", "date", "financial", "other"]
    field: str
    expected: Optional[str] = None
    found: Optional[str] = None
    page: Optional[int] = None
    severity: Literal["low", "medium", "high"] = "medium"
    notes: Optional[str] = None
    source: Optional[Literal["model", "rule"]] = None
    evidence: Optional[List[str]] = None
    confidence: Optional[float] = Field(default=None, ge=0, le=1)


class AuditReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: Optional[str] = None
    status: Literal["ok", "issues_found", "error"]
    issues: List[Discrepancy] = Field(default_factory=list)
    summary: Optional[str] = None
    review_required: bool = False
    review_reasons: List[str] = Field(default_factory=list)


ReviewStatus = Literal["pending", "in_review", "resolved"]


class ReviewItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: Optional[str] = None
    document_id: Optional[str] = None
    provider: Optional[str] = None
    status: ReviewStatus = "pending"
    summary: Optional[str] = None
    issues: List[Discrepancy] = Field(default_factory=list)
    review_required: bool = True
    review_reasons: List[str] = Field(default_factory=list)
    risk_score: Optional[float] = None
    confidence_avg: Optional[float] = None
    reviewer_notes: Optional[str] = None
    tenant_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ReviewUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Optional[ReviewStatus] = None
    reviewer_notes: Optional[str] = None


class AccuracyReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tp: int
    fp: int
    fn: int
    precision: float
    recall: float
    updated_at: Optional[str] = None
