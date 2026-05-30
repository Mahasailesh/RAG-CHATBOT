from fastapi.testclient import TestClient

from app.main import app
from app.models import AuditReport, Discrepancy
from app.services.llm.errors import ProviderAuthError


def test_health_check() -> None:
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "kb_ready" in payload


def test_audit_success(monkeypatch) -> None:
    def fake_run_audit(_, __):
        return AuditReport(
            status="issues_found",
            issues=[
                Discrepancy(
                    category="date",
                    field="passport_expiry",
                    expected="2030-01-01",
                    found="2029-01-01",
                    page=2,
                    severity="high",
                )
            ],
            summary="One date mismatch detected.",
        )

    monkeypatch.setattr("app.api.routes.run_rag_audit", fake_run_audit)
    client = TestClient(app)
    response = client.post(
        "/api/audit",
        json={
            "document_id": "doc-123",
            "provider": "gemini",
            "pages": {1: "Sample content"},
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "issues_found"
    assert payload["document_id"] == "doc-123"
    assert len(payload["issues"]) == 1


def test_audit_auth_error(monkeypatch) -> None:
    def fake_run_audit(_, __):
        raise ProviderAuthError("Provider API key not configured.")

    monkeypatch.setattr("app.api.routes.run_rag_audit", fake_run_audit)
    client = TestClient(app)
    response = client.post(
        "/api/audit",
        json={
            "document_id": "doc-123",
            "provider": "gemini",
            "pages": {1: "Sample content"},
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Provider API key not configured."
