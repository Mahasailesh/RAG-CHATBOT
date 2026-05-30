from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime
from typing import Iterable

from ...models import Discrepancy, DocumentText

LABEL_PATTERNS = {
    "full_name": {
        "category": "name",
        "labels": [
            r"\bfull name\b",
            r"\bname\b",
            r"\bapplicant name\b",
        ],
    },
    "given_name": {
        "category": "name",
        "labels": [r"\bgiven name\b", r"\bfirst name\b", r"\bforename\b"],
    },
    "surname": {
        "category": "name",
        "labels": [r"\bsurname\b", r"\blast name\b", r"\bfamily name\b"],
    },
    "date_of_birth": {
        "category": "date",
        "labels": [r"\bdate of birth\b", r"\bdob\b", r"\bbirth date\b"],
    },
    "passport_number": {
        "category": "other",
        "labels": [r"\bpassport number\b", r"\bpassport no\b", r"\bpassport #\b"],
    },
    "document_number": {
        "category": "other",
        "labels": [r"\bdocument number\b", r"\bid number\b", r"\ba-number\b"],
    },
    "issue_date": {
        "category": "date",
        "labels": [r"\bissue date\b", r"\bdate of issue\b"],
    },
    "expiry_date": {
        "category": "date",
        "labels": [r"\bexpiration date\b", r"\bexpiry date\b", r"\bvalid until\b"],
    },
    "nationality": {
        "category": "other",
        "labels": [r"\bnationality\b", r"\bcitizenship\b"],
    },
    "email": {
        "category": "other",
        "labels": [r"\bemail\b", r"\be-mail\b", r"\bemail address\b"],
    },
    "phone": {
        "category": "other",
        "labels": [r"\bphone\b", r"\btelephone\b", r"\bmobile\b", r"\bcontact number\b"],
    },
    "income": {
        "category": "financial",
        "labels": [r"\bincome\b", r"\bannual income\b", r"\bsalary\b"],
    },
    "balance": {
        "category": "financial",
        "labels": [r"\bbalance\b", r"\baccount balance\b"],
    },
}

DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%m-%d-%Y")
DATE_REGEX = re.compile(r"\b\d{2,4}[-/]\d{2}[-/]\d{2,4}\b")
ALPHANUMERIC_REGEX = re.compile(r"^[A-Za-z0-9]+$")
NAME_DIGIT_REGEX = re.compile(r"\d")
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_DIGIT_REGEX = re.compile(r"\d")
AMOUNT_REGEX = re.compile(r"[-+]?\$?\d[\d,]*(?:\.\d+)?")


def _parse_date(value: str) -> datetime | None:
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _normalize_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z]+", " ", value).strip().lower()
    return re.sub(r"\s+", " ", cleaned)


def _parse_amount(value: str) -> float | None:
    match = AMOUNT_REGEX.search(value.replace(",", ""))
    if not match:
        return None
    raw = match.group(0).replace("$", "").replace(",", "")
    try:
        return float(raw)
    except ValueError:
        return None


def _normalize_value(field_key: str, value: str) -> str:
    if field_key in {"full_name", "given_name", "surname"}:
        return _normalize_name(value)
    if field_key in {"passport_number", "document_number"}:
        return re.sub(r"[\s\-]+", "", value).lower()
    if field_key in {"income", "balance"}:
        amount = _parse_amount(value)
        return f"{amount:.2f}" if amount is not None else value.strip().lower()
    return re.sub(r"\s+", " ", value.strip()).lower()


def _extract_label_values(text: str) -> Iterable[tuple[str, str, str]]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines:
        for field_key, config in LABEL_PATTERNS.items():
            for label in config["labels"]:
                pattern = re.compile(rf"^[\s\-•*]*{label}\s*[:\-]\s*(.+)$", re.IGNORECASE)
                match = pattern.search(line)
                if match:
                    value = match.group(1).strip()
                    if value:
                        yield field_key, value, line


def run_rule_checks(payload: DocumentText) -> tuple[list[Discrepancy], list[str]]:
    values: dict[str, list[tuple[str, int, str]]] = defaultdict(list)
    issues: list[Discrepancy] = []
    review_reasons: list[str] = []
    parsed_dates: dict[str, list[tuple[datetime, int, str]]] = defaultdict(list)
    today = datetime.utcnow().date()

    for page_number, text in payload.pages.items():
        for field_key, value, line in _extract_label_values(text):
            values[field_key].append((value, page_number, line))

            if field_key in {"date_of_birth", "issue_date", "expiry_date"}:
                parsed = _parse_date(value)
                if parsed is None:
                    issues.append(
                        Discrepancy(
                            category="date",
                            field=field_key,
                            expected="valid date",
                            found=value,
                            page=page_number,
                            severity="medium",
                            notes="Unrecognized date format for labeled field.",
                            source="rule",
                            evidence=[f"Page {page_number}: {line}"],
                        )
                    )
                    review_reasons.append("Unrecognized date format detected.")
                else:
                    parsed_dates[field_key].append((parsed, page_number, line))
                    parsed_date = parsed.date()
                    if field_key == "date_of_birth" and parsed_date > today:
                        issues.append(
                            Discrepancy(
                                category="date",
                                field=field_key,
                                expected="past date",
                                found=value,
                                page=page_number,
                                severity="high",
                                notes="Date of birth occurs in the future.",
                                source="rule",
                                evidence=[f"Page {page_number}: {line}"],
                            )
                        )
                        review_reasons.append("Date of birth in the future.")
                    if field_key == "expiry_date" and parsed_date < today:
                        issues.append(
                            Discrepancy(
                                category="date",
                                field=field_key,
                                expected="future date",
                                found=value,
                                page=page_number,
                                severity="medium",
                                notes="Document appears to be expired.",
                                source="rule",
                                evidence=[f"Page {page_number}: {line}"],
                            )
                        )
                        review_reasons.append("Expired document date detected.")
                    if field_key == "issue_date" and parsed_date > today:
                        issues.append(
                            Discrepancy(
                                category="date",
                                field=field_key,
                                expected="past or present date",
                                found=value,
                                page=page_number,
                                severity="medium",
                                notes="Issue date occurs in the future.",
                                source="rule",
                                evidence=[f"Page {page_number}: {line}"],
                            )
                        )
                        review_reasons.append("Issue date in the future.")

            if field_key in {"full_name", "given_name", "surname"} and NAME_DIGIT_REGEX.search(value):
                issues.append(
                    Discrepancy(
                        category="name",
                        field=field_key,
                        expected="alphabetic name",
                        found=value,
                        page=page_number,
                        severity="low",
                        notes="Numeric characters detected in name.",
                        source="rule",
                        evidence=[f"Page {page_number}: {line}"],
                    )
                )
                review_reasons.append("Unexpected numeric characters in name.")

            if field_key in {"passport_number", "document_number"}:
                compact = value.replace(" ", "").strip()
                if len(compact) < 5 or len(compact) > 20 or not ALPHANUMERIC_REGEX.match(
                    compact
                ):
                    issues.append(
                        Discrepancy(
                            category="other",
                            field=field_key,
                            expected="valid identifier",
                            found=value,
                            page=page_number,
                            severity="medium",
                            notes="Identifier format appears invalid.",
                            source="rule",
                            evidence=[f"Page {page_number}: {line}"],
                        )
                    )
                    review_reasons.append("Identifier format issue detected.")

            if field_key == "email" and not EMAIL_REGEX.match(value):
                issues.append(
                    Discrepancy(
                        category="other",
                        field=field_key,
                        expected="valid email address",
                        found=value,
                        page=page_number,
                        severity="medium",
                        notes="Email address format appears invalid.",
                        source="rule",
                        evidence=[f"Page {page_number}: {line}"],
                    )
                )
                review_reasons.append("Invalid email address detected.")

            if field_key == "phone":
                digit_count = len(PHONE_DIGIT_REGEX.findall(value))
                if digit_count < 7 or digit_count > 15:
                    issues.append(
                        Discrepancy(
                            category="other",
                            field=field_key,
                            expected="valid phone number",
                            found=value,
                            page=page_number,
                            severity="medium",
                            notes="Phone number format appears invalid.",
                            source="rule",
                            evidence=[f"Page {page_number}: {line}"],
                        )
                    )
                    review_reasons.append("Invalid phone number detected.")

            if field_key in {"income", "balance"} and _parse_amount(value) is None:
                issues.append(
                    Discrepancy(
                        category="financial",
                        field=field_key,
                        expected="valid amount",
                        found=value,
                        page=page_number,
                        severity="medium",
                        notes="Financial value does not appear numeric.",
                        source="rule",
                        evidence=[f"Page {page_number}: {line}"],
                    )
                )
                review_reasons.append("Invalid financial amount detected.")

        for match in DATE_REGEX.findall(text):
            parsed = _parse_date(match)
            if parsed is None:
                issues.append(
                    Discrepancy(
                        category="date",
                        field="date_format",
                        expected="valid date",
                        found=match,
                        page=page_number,
                        severity="medium",
                        notes="Unrecognized date format detected by rule checks.",
                        source="rule",
                        evidence=[f"Page {page_number}: {match}"],
                    )
                )
                review_reasons.append("Unrecognized date format detected.")

    for field_key, occurrences in values.items():
        distinct = {}
        for value, page_number, line in occurrences:
            normalized = _normalize_value(field_key, value)
            distinct.setdefault(normalized, []).append((value, page_number, line))

        if len(distinct) > 1:
            category = LABEL_PATTERNS[field_key]["category"]
            seen_values = list(distinct.values())
            expected_value = seen_values[0][0][0]
            for value, page_number, line in seen_values[1]:
                issues.append(
                    Discrepancy(
                        category=category,
                        field=field_key,
                        expected=expected_value,
                        found=value,
                        page=page_number,
                        severity="high" if field_key in {"passport_number", "document_number"} else "medium",
                        notes="Inconsistent value detected across pages.",
                        source="rule",
                        evidence=[f"Page {page_number}: {line}"],
                    )
                )
                review_reasons.append(f"Inconsistent {field_key} values detected.")

    if values.get("full_name") and values.get("given_name") and values.get("surname"):
        full_value, full_page, full_line = values["full_name"][0]
        given_value, given_page, given_line = values["given_name"][0]
        surname_value, surname_page, surname_line = values["surname"][0]
        full_norm = _normalize_name(full_value)
        given_norm = _normalize_name(given_value)
        surname_norm = _normalize_name(surname_value)
        if given_norm and surname_norm:
            if given_norm not in full_norm or surname_norm not in full_norm:
                issues.append(
                    Discrepancy(
                        category="name",
                        field="full_name",
                        expected=f"{given_value} {surname_value}",
                        found=full_value,
                        page=full_page,
                        severity="medium",
                        notes="Full name does not match given name and surname.",
                        source="rule",
                        evidence=[
                            f"Page {full_page}: {full_line}",
                            f"Page {given_page}: {given_line}",
                            f"Page {surname_page}: {surname_line}",
                        ],
                    )
                )
                review_reasons.append("Full name does not match given name/surname.")

    if parsed_dates.get("issue_date") and parsed_dates.get("expiry_date"):
        for issue_date, issue_page, issue_line in parsed_dates["issue_date"]:
            for expiry_date, expiry_page, expiry_line in parsed_dates["expiry_date"]:
                if issue_date > expiry_date:
                    issues.append(
                        Discrepancy(
                            category="date",
                            field="issue_vs_expiry",
                            expected=expiry_date.strftime("%Y-%m-%d"),
                            found=issue_date.strftime("%Y-%m-%d"),
                            page=issue_page,
                            severity="high",
                            notes="Issue date occurs after expiry date.",
                            source="rule",
                            evidence=[
                                f"Page {issue_page}: {issue_line}",
                                f"Page {expiry_page}: {expiry_line}",
                            ],
                        )
                    )
                    review_reasons.append("Issue date later than expiry date.")

    return issues, sorted(set(review_reasons))
