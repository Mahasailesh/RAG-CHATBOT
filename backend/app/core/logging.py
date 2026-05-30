from __future__ import annotations

import logging


def get_logger() -> logging.Logger:
    logger = logging.getLogger("clearpass")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def log_audit_event(
    *,
    provider: str,
    status: str,
    page_count: int,
    char_count: int,
    retrieval_k: int | None,
    latency_ms: float,
    tenant_id: str | None,
) -> None:
    logger = get_logger()
    logger.info(
        "audit_request provider=%s status=%s pages=%s chars=%s retrieval_k=%s latency_ms=%.2f tenant=%s",
        provider,
        status,
        page_count,
        char_count,
        retrieval_k,
        latency_ms,
        tenant_id or "none",
    )
