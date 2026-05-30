from app.models import DocumentText
from app.services.rules import run_rule_checks


def test_rule_detects_name_digits() -> None:
    payload = DocumentText(pages={1: "Full Name: Alex C4rter"})
    issues, reasons = run_rule_checks(payload)
    assert any(issue.field == "full_name" for issue in issues)
    assert "Unexpected numeric characters in name." in reasons


def test_rule_detects_inconsistent_dates() -> None:
    payload = DocumentText(
        pages={
            1: "Date of Birth: 1990-01-01",
            2: "Date of Birth: 1990-01-02",
        }
    )
    issues, _ = run_rule_checks(payload)
    assert any(issue.field == "date_of_birth" for issue in issues)


def test_rule_issue_after_expiry() -> None:
    payload = DocumentText(
        pages={
            1: "Issue Date: 2030-01-01",
            2: "Expiry Date: 2029-01-01",
        }
    )
    issues, reasons = run_rule_checks(payload)
    assert any(issue.field == "issue_vs_expiry" for issue in issues)
    assert "Issue date later than expiry date." in reasons


def test_rule_detects_invalid_email() -> None:
    payload = DocumentText(pages={1: "Email: not-an-email"})
    issues, reasons = run_rule_checks(payload)
    assert any(issue.field == "email" for issue in issues)
    assert "Invalid email address detected." in reasons


def test_rule_detects_full_name_mismatch() -> None:
    payload = DocumentText(
        pages={
            1: "Full Name: Alex Carter\nGiven Name: Alex\nSurname: Karter",
        }
    )
    issues, reasons = run_rule_checks(payload)
    assert any(issue.field == "full_name" for issue in issues)
    assert "Full name does not match given name/surname." in reasons
