from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta
import hashlib
import logging
import re
import time
from typing import Iterable, Sequence
from urllib.parse import urldefrag, urljoin, urlparse

import fitz
from bs4 import BeautifulSoup
from email.message import EmailMessage
import httpx
from openai import OpenAI
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright
import smtplib
from supabase import create_client

from config import (
    ALERT_EMAIL_FROM,
    ALERT_EMAIL_TO,
    ALERT_MIN_INTERVAL_SECONDS,
    ALERT_SMTP_HOST,
    ALERT_SMTP_PASSWORD,
    ALERT_SMTP_PORT,
    ALERT_SMTP_TLS,
    ALERT_SMTP_USER,
    ALERT_WEBHOOK_URL,
    EMBEDDING_MODEL,
    LOG_FAILURES,
    OPENAI_API_KEY,
    PLAYWRIGHT_HEADLESS,
    REQUEST_BACKOFF_SECONDS,
    REQUEST_DELAY_SECONDS,
    REQUEST_RETRIES,
    RETENTION_DAYS,
    SCHEDULE_INTERVAL_HOURS,
    SUPABASE_KEY,
    SUPABASE_URL,
    TARGETS,
    TargetConfig,
    USER_AGENT,
)

TABLE_NAME = "immigration_knowledge_base"
FAILURE_TABLE_NAME = "ingestion_failures"
REQUEST_TIMEOUT_MS = 30_000
CHUNK_MIN_WORDS = 500
CHUNK_MAX_WORDS = 800
CHUNK_OVERLAP_RATIO = 0.1
EMBED_BATCH_SIZE = 96
_LAST_ALERT_AT: dict[str, float] = {}


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )


def ensure_env() -> None:
    missing = []
    if not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")
    if not SUPABASE_URL:
        missing.append("SUPABASE_URL")
    if not SUPABASE_KEY:
        missing.append("SUPABASE_KEY")
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")


async def log_failure(
    supabase,
    stage: str,
    target_name: str | None = None,
    source_url: str | None = None,
    document_url: str | None = None,
    error: Exception | None = None,
) -> None:
    payload = {
        "target_name": target_name,
        "source_url": source_url,
        "document_url": document_url,
        "stage": stage,
        "error_type": type(error).__name__ if error else None,
        "error_message": str(error) if error else None,
        "alert_time": datetime.utcnow().isoformat(),
    }

    if LOG_FAILURES and supabase is not None:
        def _insert():
            return supabase.table(FAILURE_TABLE_NAME).insert(payload).execute()

        try:
            await asyncio.to_thread(_insert)
        except Exception as exc:
            logging.info("Failure log insert failed: %s", exc)

    await send_alert(payload)


def _should_alert(payload: dict) -> bool:
    if not ALERT_WEBHOOK_URL and not ALERT_EMAIL_TO:
        return False
    key_parts = [
        payload.get("stage"),
        payload.get("target_name"),
        payload.get("document_url") or payload.get("source_url"),
    ]
    key = "|".join(part for part in key_parts if part)
    now = time.monotonic()
    last_at = _LAST_ALERT_AT.get(key, 0.0)
    if now - last_at < ALERT_MIN_INTERVAL_SECONDS:
        return False
    _LAST_ALERT_AT[key] = now
    return True


async def send_alert(payload: dict) -> None:
    if not _should_alert(payload):
        return
    if ALERT_WEBHOOK_URL:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(ALERT_WEBHOOK_URL, json=payload)
        except Exception as exc:
            logging.info("Alert webhook failed: %s", exc)

    if ALERT_EMAIL_TO:
        await send_email_alert(payload)


async def send_email_alert(payload: dict) -> None:
    if not ALERT_SMTP_HOST or not ALERT_EMAIL_FROM:
        logging.info("Email alert skipped: missing SMTP host or from address.")
        return
    recipients = [addr.strip() for addr in ALERT_EMAIL_TO.split(",") if addr.strip()] if ALERT_EMAIL_TO else []
    if not recipients:
        return

    subject = f"ClearPass ingestion failure: {payload.get('stage')}"
    lines = [
        f"Target: {payload.get('target_name')}",
        f"Stage: {payload.get('stage')}",
        f"Source URL: {payload.get('source_url')}",
        f"Document URL: {payload.get('document_url')}",
        f"Error Type: {payload.get('error_type')}",
        f"Error Message: {payload.get('error_message')}",
        f"Time (UTC): {payload.get('alert_time')}",
    ]
    body = "\n".join(line for line in lines if line and "None" not in line)

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = ALERT_EMAIL_FROM
    message["To"] = ", ".join(recipients)
    message.set_content(body)

    def _send():
        if ALERT_SMTP_TLS:
            server = smtplib.SMTP(ALERT_SMTP_HOST, ALERT_SMTP_PORT, timeout=10)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(ALERT_SMTP_HOST, ALERT_SMTP_PORT, timeout=10)
        try:
            if ALERT_SMTP_USER and ALERT_SMTP_PASSWORD:
                server.login(ALERT_SMTP_USER, ALERT_SMTP_PASSWORD)
            server.send_message(message)
        finally:
            server.quit()

    try:
        await asyncio.to_thread(_send)
    except Exception as exc:
        logging.info("Email alert failed: %s", exc)


def normalize_whitespace(text: str) -> str:
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def parse_date(text: str) -> date | None:
    if not text:
        return None
    text = text.strip()
    patterns = [
        r"(\d{4}-\d{2}-\d{2})",
        r"([A-Za-z]+\s+\d{1,2},\s+\d{4})",
        r"(\d{1,2}\s+[A-Za-z]+\s+\d{4})",
    ]
    candidate = None
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            candidate = match.group(1)
            break
    candidate = candidate or text
    formats = ["%Y-%m-%d", "%B %d, %Y", "%b %d, %Y", "%d %B %Y"]
    for fmt in formats:
        try:
            return datetime.strptime(candidate, fmt).date()
        except ValueError:
            continue
    return None


def find_updated_date_from_text(text: str) -> date | None:
    if not text:
        return None
    patterns = [
        r"Last updated\s*[:\-]?\s*(?P<date>\w+\s+\d{1,2},\s+\d{4})",
        r"Date modified\s*[:\-]?\s*(?P<date>\w+\s+\d{1,2},\s+\d{4})",
        r"Last updated\s*[:\-]?\s*(?P<date>\d{4}-\d{2}-\d{2})",
        r"Date modified\s*[:\-]?\s*(?P<date>\d{4}-\d{2}-\d{2})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return parse_date(match.group("date"))
    return None


def detect_captcha(text: str) -> bool:
    if not text:
        return False
    lowered = text.lower()
    triggers = ["captcha", "are you human", "verify you are", "robot"]
    return any(trigger in lowered for trigger in triggers)


def extract_main_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside", "form"]):
        tag.decompose()

    main = soup.find("main") or soup.find("article") or soup.body
    if not main:
        return ""

    text = main.get_text(separator="\n")
    return normalize_whitespace(text)


def discover_document_links(
    html: str,
    base_url: str,
    patterns: Sequence[str],
    keywords: Sequence[str],
) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links: list[str] = []
    seen: set[str] = set()
    regexes = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    keyword_lc = [keyword.lower() for keyword in keywords]

    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        if not href:
            continue
        url = normalize_url(urljoin(base_url, href))
        if url in seen:
            continue
        text = anchor.get_text(strip=True).lower()
        if regexes and any(regex.search(url) for regex in regexes):
            links.append(url)
            seen.add(url)
            continue
        if url.lower().endswith(".pdf"):
            if not keyword_lc or any(k in text or k in url.lower() for k in keyword_lc):
                links.append(url)
                seen.add(url)
    return links


def normalize_url(url: str) -> str:
    cleaned, _ = urldefrag(url)
    return cleaned.rstrip("/")


def extract_internal_links(
    html: str,
    base_url: str,
    root_netloc: str,
    allow_patterns: Sequence[str],
    deny_patterns: Sequence[str],
) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links: list[str] = []
    allow_regex = [re.compile(pattern, re.IGNORECASE) for pattern in allow_patterns]
    deny_regex = [re.compile(pattern, re.IGNORECASE) for pattern in deny_patterns]
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        if not href or href.startswith("#"):
            continue
        if href.startswith(("mailto:", "tel:", "javascript:")):
            continue
        url = normalize_url(urljoin(base_url, href))
        parsed = urlparse(url)
        if parsed.netloc != root_netloc:
            continue
        if re.search(r"\.(pdf|zip|docx?|xlsx?|pptx?|jpg|jpeg|png|gif)$", parsed.path, re.IGNORECASE):
            continue
        if allow_regex and not any(regex.search(url) for regex in allow_regex):
            continue
        if deny_regex and any(regex.search(url) for regex in deny_regex):
            continue
        links.append(url)
    return links


def chunk_legal_text(raw_text: str) -> list[str]:
    paragraphs = [para.strip() for para in raw_text.split("\n\n") if para.strip()]
    chunks: list[str] = []
    current: list[str] = []
    current_words = 0

    def flush_chunk() -> None:
        nonlocal current, current_words
        if not current:
            return
        chunk_text = "\n\n".join(current)
        chunks.append(chunk_text)
        words = re.findall(r"\b\w+\b", chunk_text)
        overlap_words = max(1, int(len(words) * CHUNK_OVERLAP_RATIO))
        overlap_text = " ".join(words[-overlap_words:]) if words else ""
        current = [overlap_text] if overlap_text else []
        current_words = len(re.findall(r"\b\w+\b", overlap_text))

    for paragraph in paragraphs:
        paragraph_words = len(re.findall(r"\b\w+\b", paragraph))
        if current_words + paragraph_words > CHUNK_MAX_WORDS and current_words >= CHUNK_MIN_WORDS:
            flush_chunk()
        current.append(paragraph)
        current_words += paragraph_words

    if current:
        chunks.append("\n\n".join(current))

    return chunks


def compute_md5(payload: bytes) -> str:
    return hashlib.md5(payload).hexdigest()


async def apply_delay() -> None:
    if REQUEST_DELAY_SECONDS > 0:
        await asyncio.sleep(REQUEST_DELAY_SECONDS)


async def run_with_retries(operation, label: str):
    attempt = 0
    while True:
        try:
            return await operation()
        except PlaywrightTimeoutError:
            logging.warning("Timeout while %s", label)
        except Exception as exc:
            logging.warning("Error while %s: %s", label, exc)

        if attempt >= REQUEST_RETRIES:
            logging.error("Giving up on %s after %s retries", label, REQUEST_RETRIES)
            return None
        wait = REQUEST_BACKOFF_SECONDS * (2 ** attempt)
        attempt += 1
        logging.info("Retrying %s in %.2f seconds", label, wait)
        await asyncio.sleep(wait)


async def fetch_page_html(
    page,
    url: str,
    supabase=None,
    target_name: str | None = None,
    source_url: str | None = None,
) -> str | None:
    async def _load():
        await apply_delay()
        await page.goto(url, wait_until="domcontentloaded", timeout=REQUEST_TIMEOUT_MS)
        body_text = await page.inner_text("body")
        if detect_captcha(body_text):
            logging.critical("CAPTCHA detected for %s", url)
            await log_failure(
                supabase,
                stage="captcha",
                target_name=target_name,
                source_url=source_url or url,
                document_url=url,
            )
            return None
        return await page.content()

    html = await run_with_retries(_load, f"loading {url}")
    if html is None:
        await log_failure(
            supabase,
            stage="fetch_html",
            target_name=target_name,
            source_url=source_url or url,
            document_url=url,
        )
    return html


async def crawl_internal_pages(target: TargetConfig, page, supabase) -> dict[str, str]:
    root = normalize_url(target.target_url)
    root_netloc = urlparse(root).netloc
    max_depth = max(0, target.crawl_max_depth)
    max_pages = max(1, target.crawl_max_pages)

    queue: list[tuple[str, int]] = [(root, 0)]
    visited: set[str] = set()
    html_map: dict[str, str] = {}

    while queue and len(visited) < max_pages:
        current_url, depth = queue.pop(0)
        if current_url in visited:
            continue
        visited.add(current_url)

        html = await fetch_page_html(
            page,
            current_url,
            supabase=supabase,
            target_name=target.name,
            source_url=target.target_url,
        )
        if not html:
            continue
        html_map[current_url] = html

        if depth >= max_depth:
            continue
        for link in extract_internal_links(
            html,
            current_url,
            root_netloc,
            target.crawl_allow_patterns,
            target.crawl_deny_patterns,
        ):
            if link not in visited and len(visited) + len(queue) < max_pages:
                queue.append((link, depth + 1))

    return html_map

async def check_for_updates(
    page,
    supabase,
    target_url: str,
    selectors: Sequence[str],
    target_name: str | None = None,
) -> tuple[bool, date | None]:
    try:
        html = await fetch_page_html(
            page,
            target_url,
            supabase=supabase,
            target_name=target_name,
            source_url=target_url,
        )
        if not html:
            return False, None
        body_text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
        if detect_captcha(body_text):
            logging.critical("CAPTCHA detected for %s", target_url)
            return False, None

        last_updated_text = None
        for selector in selectors:
            try:
                locator = page.locator(selector).first
                if await locator.count() == 0:
                    continue
                text = await locator.text_content()
                attr = await locator.get_attribute("datetime")
                if not attr:
                    attr = await locator.get_attribute("content")
                if text and text.strip():
                    last_updated_text = text.strip()
                    break
                if attr and attr.strip():
                    last_updated_text = attr.strip()
                    break
            except Exception:
                continue

        last_updated = parse_date(last_updated_text) if last_updated_text else None
        if not last_updated:
            last_updated = find_updated_date_from_text(body_text)

        if not last_updated:
            logging.info("No last updated date found for %s; relying on document hashes.", target_url)
            return True, None

        def _fetch_latest():
            return (
                supabase.table(TABLE_NAME)
                .select("last_updated_date")
                .eq("source_url", target_url)
                .order("last_updated_date", desc=True)
                .limit(1)
                .execute()
            )

        response = await asyncio.to_thread(_fetch_latest)
        if response.data:
            latest = response.data[0].get("last_updated_date")
            if latest:
                latest_date = datetime.strptime(latest, "%Y-%m-%d").date()
                if last_updated <= latest_date:
                    logging.info("No updates found for %s", target_url)
                    return False, last_updated

        return True, last_updated
    except PlaywrightTimeoutError:
        logging.critical("Timeout while loading %s", target_url)
        await log_failure(
            supabase,
            stage="timeout",
            target_name=target_name,
            source_url=target_url,
            document_url=target_url,
        )
        return False, None
    except Exception as exc:
        logging.error("Update check failed for %s error=%s", target_url, exc)
        await log_failure(
            supabase,
            stage="update_check",
            target_name=target_name,
            source_url=target_url,
            document_url=target_url,
            error=exc,
        )
        return False, None


async def process_document(
    page,
    context,
    file_url: str,
    file_type: str,
    html: str | None = None,
    supabase=None,
    target_name: str | None = None,
    source_url: str | None = None,
) -> tuple[str, str] | None:
    try:
        if file_type == "pdf":
            async def _download():
                await apply_delay()
                return await context.request.get(file_url, timeout=REQUEST_TIMEOUT_MS)

            response = await run_with_retries(_download, f"downloading PDF {file_url}")
            if response is None or response.status >= 400:
                status = response.status if response else "unknown"
                logging.error("Failed to download PDF %s status=%s", file_url, status)
                await log_failure(
                    supabase,
                    stage="download_pdf",
                    target_name=target_name,
                    source_url=source_url,
                    document_url=file_url,
                    error=RuntimeError(f"status={status}"),
                )
                return None
            payload = await response.body()
            document_hash = compute_md5(payload)
            doc = fitz.open(stream=payload, filetype="pdf")
            text_parts = [page.get_text("text") for page in doc]
            doc.close()
            raw_text = normalize_whitespace("\n\n".join(text_parts))
            return raw_text, document_hash

        if file_type == "html":
            if html is None:
                html = await fetch_page_html(
                    page,
                    file_url,
                    supabase=supabase,
                    target_name=target_name,
                    source_url=source_url or file_url,
                )
                if not html:
                    return None
            payload = html.encode("utf-8")
            document_hash = compute_md5(payload)
            raw_text = extract_main_text(html)
            return raw_text, document_hash

        logging.error("Unsupported file type for %s", file_url)
        await log_failure(
            supabase,
            stage="unsupported_type",
            target_name=target_name,
            source_url=source_url,
            document_url=file_url,
        )
        return None
    except PlaywrightTimeoutError:
        logging.critical("Timeout while fetching %s", file_url)
        await log_failure(
            supabase,
            stage="timeout",
            target_name=target_name,
            source_url=source_url,
            document_url=file_url,
        )
        return None
    except Exception as exc:
        logging.error("Failed to process document %s error=%s", file_url, exc)
        await log_failure(
            supabase,
            stage="process_document",
            target_name=target_name,
            source_url=source_url,
            document_url=file_url,
            error=exc,
        )
        return None


def build_rows(
    chunks: Sequence[str],
    embeddings: Sequence[Sequence[float]],
    metadata: dict,
) -> list[dict]:
    rows = []
    for chunk, embedding in zip(chunks, embeddings):
        rows.append(
            {
                "country": metadata["country"],
                "form_type": metadata["form_type"],
                "source_url": metadata["source_url"],
                "document_url": metadata.get("document_url"),
                "page_url": metadata.get("page_url"),
                "last_updated_date": metadata.get("last_updated_date"),
                "document_hash": metadata["document_hash"],
                "content_chunk": chunk,
                "embedding": embedding,
            }
        )
    return rows


async def embed_and_store(
    chunks: Sequence[str],
    metadata: dict,
    supabase,
    openai: OpenAI,
    target_name: str | None = None,
) -> None:
    if not chunks:
        logging.info("No chunks to store for %s", metadata.get("source_url"))
        return

    for start in range(0, len(chunks), EMBED_BATCH_SIZE):
        batch = chunks[start : start + EMBED_BATCH_SIZE]

        def _embed():
            return openai.embeddings.create(model=EMBEDDING_MODEL, input=batch)

        try:
            response = await asyncio.to_thread(_embed)
            embeddings = [item.embedding for item in response.data]
        except Exception as exc:
            logging.error("Embedding failed for %s error=%s", metadata.get("source_url"), exc)
            await log_failure(
                supabase,
                stage="embedding",
                target_name=target_name,
                source_url=metadata.get("source_url"),
                document_url=metadata.get("document_url"),
                error=exc,
            )
            return
        rows = build_rows(batch, embeddings, metadata)

        def _insert():
            return supabase.table(TABLE_NAME).insert(rows).execute()

        try:
            await asyncio.to_thread(_insert)
        except Exception as exc:
            logging.error("Insert failed for %s error=%s", metadata.get("source_url"), exc)
            await log_failure(
                supabase,
                stage="insert",
                target_name=target_name,
                source_url=metadata.get("source_url"),
                document_url=metadata.get("document_url"),
                error=exc,
            )
            return

    logging.info(
        "Inserted %s chunks for %s",
        len(chunks),
        metadata.get("source_url"),
    )


async def has_hash(
    supabase,
    document_url: str,
    document_hash: str,
    source_url: str | None = None,
) -> bool:
    def _query():
        return (
            supabase.table(TABLE_NAME)
            .select("id")
            .eq("document_url", document_url)
            .eq("document_hash", document_hash)
            .limit(1)
            .execute()
        )

    response = await asyncio.to_thread(_query)
    if response.data:
        return True
    if source_url:
        def _fallback():
            return (
                supabase.table(TABLE_NAME)
                .select("id")
                .eq("source_url", source_url)
                .eq("document_hash", document_hash)
                .limit(1)
                .execute()
            )

        fallback = await asyncio.to_thread(_fallback)
        return bool(fallback.data)
    return False


async def cleanup_old_versions(supabase, document_url: str, document_hash: str) -> None:
    def _delete():
        return (
            supabase.table(TABLE_NAME)
            .delete()
            .eq("document_url", document_url)
            .neq("document_hash", document_hash)
            .execute()
        )

    await asyncio.to_thread(_delete)


async def prune_stale_records(supabase) -> None:
    if RETENTION_DAYS <= 0:
        return
    cutoff = datetime.utcnow() - timedelta(days=RETENTION_DAYS)
    cutoff_iso = cutoff.isoformat()

    def _delete_created():
        return (
            supabase.table(TABLE_NAME)
            .delete()
            .lt("created_at", cutoff_iso)
            .execute()
        )

    def _delete_updated():
        return (
            supabase.table(TABLE_NAME)
            .delete()
            .lt("last_updated_date", cutoff.date().isoformat())
            .execute()
        )

    try:
        await asyncio.to_thread(_delete_created)
        await asyncio.to_thread(_delete_updated)
        logging.info("Pruned records older than %s days", RETENTION_DAYS)
    except Exception as exc:
        logging.error("Pruning failed error=%s", exc)
        await log_failure(
            supabase,
            stage="prune",
            target_name=None,
            source_url=None,
            document_url=None,
            error=exc,
        )


async def run_target(target: TargetConfig, context, supabase, openai: OpenAI) -> None:
    page = await context.new_page()
    try:
        should_process, last_updated = await check_for_updates(
            page,
            supabase,
            target.target_url,
            target.last_updated_selectors,
            target_name=target.name,
        )
        if not should_process:
            return
        html_map: dict[str, str] = {}
        if target.crawl_internal_links:
            html_map = await crawl_internal_pages(target, page, supabase)
            logging.info("Crawled %s pages for %s", len(html_map), target.name)
        if not html_map:
            html = await fetch_page_html(
                page,
                target.target_url,
                supabase=supabase,
                target_name=target.name,
                source_url=target.target_url,
            )
            if html:
                html_map[target.target_url] = html

        document_links: set[str] = set()
        pdf_documents: list[tuple[str, str]] = []
        documents: list[tuple[str, str, str | None, str]] = []

        for page_url, html in html_map.items():
            if target.include_html:
                documents.append((page_url, "html", html, page_url))
            for link in discover_document_links(
                html,
                page_url,
                target.document_link_patterns,
                target.document_link_keywords,
            ):
                if link not in document_links:
                    document_links.add(link)
                    pdf_documents.append((link, page_url))

        for link, page_url in pdf_documents:
            documents.append((link, "pdf", None, page_url))

        logging.info("Processing %s with %s documents", target.name, len(documents))

        for file_url, file_type, html, page_url in documents:
            result = await process_document(
                page,
                context,
                file_url,
                file_type,
                html=html,
                supabase=supabase,
                target_name=target.name,
                source_url=target.target_url,
            )
            if not result:
                continue
            raw_text, document_hash = result
            if await has_hash(supabase, file_url, document_hash, source_url=target.target_url):
                logging.info("Document already processed for %s", file_url)
                continue
            await cleanup_old_versions(supabase, file_url, document_hash)
            chunks = chunk_legal_text(raw_text)
            metadata = {
                "country": target.country,
                "form_type": target.form_type,
                "source_url": target.target_url,
                "document_url": file_url,
                "page_url": page_url,
                "last_updated_date": last_updated.isoformat() if last_updated else None,
                "document_hash": document_hash,
            }
            await embed_and_store(chunks, metadata, supabase, openai, target_name=target.name)
    except Exception as exc:
        logging.error("Failed to run target %s error=%s", target.name, exc)
        await log_failure(
            supabase,
            stage="target",
            target_name=target.name,
            source_url=target.target_url,
            document_url=None,
            error=exc,
        )
    finally:
        await page.close()


async def run_ingestion_once() -> None:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    openai = OpenAI(api_key=OPENAI_API_KEY)

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=PLAYWRIGHT_HEADLESS)
        context = await browser.new_context(user_agent=USER_AGENT)
        try:
            for target in TARGETS:
                await run_target(target, context, supabase, openai)
            await prune_stale_records(supabase)
        finally:
            await context.close()
            await browser.close()


async def main() -> None:
    setup_logging()
    ensure_env()

    interval_hours = max(0.0, SCHEDULE_INTERVAL_HOURS)
    if interval_hours <= 0:
        await run_ingestion_once()
        return

    logging.info("Scheduler enabled with interval %.2f hours", interval_hours)
    while True:
        start_time = datetime.utcnow()
        try:
            await run_ingestion_once()
        except Exception as exc:
            logging.error("Ingestion cycle failed error=%s", exc)

        elapsed = (datetime.utcnow() - start_time).total_seconds()
        sleep_seconds = max(0.0, interval_hours * 3600 - elapsed)
        logging.info("Sleeping for %.2f hours", sleep_seconds / 3600)
        await asyncio.sleep(sleep_seconds)


if __name__ == "__main__":
    asyncio.run(main())
