from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .config import ACCURACY_REPORT_PATH
from ..models import AccuracyReport


def load_accuracy_report(path: Path | None = None) -> AccuracyReport | None:
    report_path = path or ACCURACY_REPORT_PATH
    if not report_path.exists():
        return None
    data = json.loads(report_path.read_text(encoding="utf-8"))
    if "updated_at" not in data:
        data["updated_at"] = datetime.utcfromtimestamp(report_path.stat().st_mtime).isoformat()
    return AccuracyReport.model_validate(data)
