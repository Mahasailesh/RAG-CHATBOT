from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Sequence

from dotenv import load_dotenv

_backend_dir = Path(__file__).resolve().parents[1]
_env_path = _backend_dir / ".env"
load_dotenv(_env_path)
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
PLAYWRIGHT_HEADLESS = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() not in ("false", "0", "no")
SCHEDULE_INTERVAL_HOURS = float(os.getenv("SCHEDULE_INTERVAL_HOURS", "0") or 0)

EMBEDDING_MODEL = "text-embedding-3-small"
REQUEST_RETRIES = int(os.getenv("SCRAPER_REQUEST_RETRIES", "2"))
REQUEST_BACKOFF_SECONDS = float(os.getenv("SCRAPER_REQUEST_BACKOFF_SECONDS", "1.5"))
REQUEST_DELAY_SECONDS = float(os.getenv("SCRAPER_REQUEST_DELAY_SECONDS", "0.3"))
LOG_FAILURES = os.getenv("SCRAPER_LOG_FAILURES", "true").lower() not in ("false", "0", "no")
RETENTION_DAYS = int(os.getenv("SCRAPER_RETENTION_DAYS", "0"))
ALERT_WEBHOOK_URL = os.getenv("SCRAPER_ALERT_WEBHOOK_URL", "").strip() or None
ALERT_MIN_INTERVAL_SECONDS = float(os.getenv("SCRAPER_ALERT_MIN_INTERVAL_SECONDS", "300"))
ALERT_EMAIL_TO = os.getenv("SCRAPER_ALERT_EMAIL_TO", "").strip() or None
ALERT_EMAIL_FROM = os.getenv("SCRAPER_ALERT_EMAIL_FROM", "").strip() or None
ALERT_SMTP_HOST = os.getenv("SCRAPER_ALERT_SMTP_HOST", "").strip() or None
ALERT_SMTP_PORT = int(os.getenv("SCRAPER_ALERT_SMTP_PORT", "587"))
ALERT_SMTP_USER = os.getenv("SCRAPER_ALERT_SMTP_USER", "").strip() or None
ALERT_SMTP_PASSWORD = os.getenv("SCRAPER_ALERT_SMTP_PASSWORD", "").strip() or None
ALERT_SMTP_TLS = os.getenv("SCRAPER_ALERT_SMTP_TLS", "true").lower() not in ("false", "0", "no")
USER_AGENT = os.getenv(
    "SCRAPER_USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
)

@dataclass(frozen=True)
class TargetConfig:
    name: str
    country: str
    form_type: str
    target_url: str
    last_updated_selectors: Sequence[str] = field(default_factory=tuple)
    include_html: bool = True
    document_link_patterns: Sequence[str] = field(default_factory=tuple)
    document_link_keywords: Sequence[str] = field(default_factory=tuple)
    crawl_internal_links: bool = False
    crawl_max_depth: int = 1
    crawl_max_pages: int = 25
    crawl_allow_patterns: Sequence[str] = field(default_factory=tuple)
    crawl_deny_patterns: Sequence[str] = field(default_factory=tuple)


USCIS_SELECTORS = (
    "time[datetime]",
    "meta[property='dateModified']",
    "meta[name='last-modified']",
    "[class*='last-updated']",
    "[class*='date']",
)

IRCC_SELECTORS = (
    "time[property='dateModified']",
    "time[datetime]",
    "meta[property='dateModified']",
    "[class*='modified']",
)

TARGETS: Sequence[TargetConfig] = [
    TargetConfig(
        name="USCIS I-485",
        country="US",
        form_type="I-485",
        target_url="https://www.uscis.gov/i-485",
        last_updated_selectors=USCIS_SELECTORS,
        include_html=True,
        crawl_internal_links=True,
        crawl_max_depth=1,
        crawl_max_pages=25,
        crawl_allow_patterns=(r"^https://www\.uscis\.gov/",),
        document_link_patterns=(r"i-485.*\.pdf", r"form-i-485.*\.pdf"),
        document_link_keywords=("I-485", "Form I-485", "Instructions"),
    ),
    TargetConfig(
        name="USCIS I-130",
        country="US",
        form_type="I-130",
        target_url="https://www.uscis.gov/i-130",
        last_updated_selectors=USCIS_SELECTORS,
        include_html=True,
        crawl_internal_links=True,
        crawl_max_depth=1,
        crawl_max_pages=25,
        crawl_allow_patterns=(r"^https://www\.uscis\.gov/",),
        document_link_patterns=(r"i-130.*\.pdf", r"i-130a.*\.pdf"),
        document_link_keywords=("I-130", "I-130A", "Instructions"),
    ),
    TargetConfig(
        name="USCIS I-765",
        country="US",
        form_type="I-765",
        target_url="https://www.uscis.gov/i-765",
        last_updated_selectors=USCIS_SELECTORS,
        include_html=True,
        crawl_internal_links=True,
        crawl_max_depth=1,
        crawl_max_pages=25,
        crawl_allow_patterns=(r"^https://www\.uscis\.gov/",),
        document_link_patterns=(r"i-765.*\.pdf",),
        document_link_keywords=("I-765", "Instructions"),
    ),
    TargetConfig(
        name="USCIS I-864",
        country="US",
        form_type="I-864",
        target_url="https://www.uscis.gov/i-864",
        last_updated_selectors=USCIS_SELECTORS,
        include_html=True,
        crawl_internal_links=True,
        crawl_max_depth=1,
        crawl_max_pages=25,
        crawl_allow_patterns=(r"^https://www\.uscis\.gov/",),
        document_link_patterns=(r"i-864.*\.pdf",),
        document_link_keywords=("I-864", "Instructions"),
    ),
    TargetConfig(
        name="USCIS I-131",
        country="US",
        form_type="I-131",
        target_url="https://www.uscis.gov/i-131",
        last_updated_selectors=USCIS_SELECTORS,
        include_html=True,
        crawl_internal_links=True,
        crawl_max_depth=1,
        crawl_max_pages=25,
        crawl_allow_patterns=(r"^https://www\.uscis\.gov/",),
        document_link_patterns=(r"i-131.*\.pdf",),
        document_link_keywords=("I-131", "Instructions"),
    ),
    TargetConfig(
        name="USCIS N-400",
        country="US",
        form_type="N-400",
        target_url="https://www.uscis.gov/n-400",
        last_updated_selectors=USCIS_SELECTORS,
        include_html=True,
        crawl_internal_links=True,
        crawl_max_depth=1,
        crawl_max_pages=25,
        crawl_allow_patterns=(r"^https://www\.uscis\.gov/",),
        document_link_patterns=(r"n-400.*\.pdf",),
        document_link_keywords=("N-400", "Instructions"),
    ),
    TargetConfig(
        name="USCIS Filing Fees",
        country="US",
        form_type="Filing Fees",
        target_url="https://www.uscis.gov/forms/filing-fees",
        last_updated_selectors=USCIS_SELECTORS,
        include_html=True,
        crawl_internal_links=True,
        crawl_max_depth=1,
        crawl_max_pages=25,
        crawl_allow_patterns=(r"^https://www\.uscis\.gov/",),
    ),
    TargetConfig(
        name="USCIS Forms Updates",
        country="US",
        form_type="Forms Updates",
        target_url="https://www.uscis.gov/forms/forms-updates",
        last_updated_selectors=USCIS_SELECTORS,
        include_html=True,
        crawl_internal_links=True,
        crawl_max_depth=1,
        crawl_max_pages=25,
        crawl_allow_patterns=(r"^https://www\.uscis\.gov/",),
    ),
    TargetConfig(
        name="IRCC Express Entry",
        country="Canada",
        form_type="Express Entry",
        target_url="https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/express-entry.html",
        last_updated_selectors=IRCC_SELECTORS,
        include_html=True,
        crawl_internal_links=True,
        crawl_max_depth=1,
        crawl_max_pages=25,
        crawl_allow_patterns=(
            r"^https://www\.canada\.ca/en/immigration-refugees-citizenship/",
        ),
        document_link_patterns=(r"express-entry.*\.pdf", r"imm\d+.*\.pdf"),
        document_link_keywords=("Express Entry", "IMM", "document"),
    ),
    TargetConfig(
        name="IRCC Express Entry Documents",
        country="Canada",
        form_type="Express Entry Documents",
        target_url="https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/express-entry/apply-permanent-residence/documents.html",
        last_updated_selectors=IRCC_SELECTORS,
        include_html=True,
        crawl_internal_links=True,
        crawl_max_depth=1,
        crawl_max_pages=25,
        crawl_allow_patterns=(
            r"^https://www\.canada\.ca/en/immigration-refugees-citizenship/",
        ),
        document_link_patterns=(r"imm\d+.*\.pdf",),
        document_link_keywords=("IMM", "document", "checklist"),
    ),
    TargetConfig(
        name="IRCC Application Forms and Guides",
        country="Canada",
        form_type="Forms and Guides",
        target_url="https://www.canada.ca/en/immigration-refugees-citizenship/services/application/application-forms-guides.html",
        last_updated_selectors=IRCC_SELECTORS,
        include_html=True,
        crawl_internal_links=True,
        crawl_max_depth=1,
        crawl_max_pages=25,
        crawl_allow_patterns=(
            r"^https://www\.canada\.ca/en/immigration-refugees-citizenship/",
        ),
        document_link_patterns=(r"imm\d+.*\.pdf",),
        document_link_keywords=("IMM", "guide", "application"),
    ),
    TargetConfig(
        name="IRCC Fees",
        country="Canada",
        form_type="Fees",
        target_url="https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/fees/fees-pr.html",
        last_updated_selectors=IRCC_SELECTORS,
        include_html=True,
        crawl_internal_links=True,
        crawl_max_depth=1,
        crawl_max_pages=25,
        crawl_allow_patterns=(
            r"^https://www\.canada\.ca/en/immigration-refugees-citizenship/",
        ),
    ),
    TargetConfig(
        name="IRCC Proof of Funds",
        country="Canada",
        form_type="Proof of Funds",
        target_url="https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/express-entry/eligibility/funds.html",
        last_updated_selectors=IRCC_SELECTORS,
        include_html=True,
        crawl_internal_links=True,
        crawl_max_depth=1,
        crawl_max_pages=25,
        crawl_allow_patterns=(
            r"^https://www\.canada\.ca/en/immigration-refugees-citizenship/",
        ),
    ),
]
