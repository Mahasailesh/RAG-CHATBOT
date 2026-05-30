from __future__ import annotations

from collections import Counter
from threading import Lock

_lock = Lock()
_counters = Counter()


def record_audit(
    provider: str,
    status: str,
    issue_count: int,
    review_required: bool,
    high_severity_count: int,
) -> None:
    with _lock:
        _counters["requests_total"] += 1
        _counters[f"provider:{provider}"] += 1
        _counters[f"status:{status}"] += 1
        _counters["issues_total"] += issue_count
        _counters["high_severity_total"] += high_severity_count
        if review_required:
            _counters["review_required_total"] += 1


def snapshot_metrics() -> dict:
    with _lock:
        return dict(_counters)
