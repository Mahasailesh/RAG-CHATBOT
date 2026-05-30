from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

import httpx


@dataclass(frozen=True)
class IssueKey:
    category: str
    field: str
    expected: str | None
    found: str | None


def _load_dataset(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def _issue_key(issue: dict) -> IssueKey:
    return IssueKey(
        category=str(issue.get("category", "")).strip().lower(),
        field=str(issue.get("field", "")).strip().lower(),
        expected=(issue.get("expected") or None),
        found=(issue.get("found") or None),
    )


def _score(expected: Iterable[IssueKey], predicted: Iterable[IssueKey]) -> dict:
    expected_set = set(expected)
    predicted_set = set(predicted)
    tp = len(expected_set & predicted_set)
    fp = len(predicted_set - expected_set)
    fn = len(expected_set - predicted_set)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
    }


def evaluate(
    api_base: str,
    dataset_path: Path,
    byok_key: str | None,
    provider: str | None,
) -> dict:
    dataset = _load_dataset(dataset_path)
    totals = {"tp": 0, "fp": 0, "fn": 0, "precision": 0.0, "recall": 0.0}
    client = httpx.Client(timeout=120)
    for entry in dataset:
        expected_keys = [_issue_key(item) for item in entry.get("expected_issues", [])]
        payload = {
            "document_id": entry.get("document_id"),
            "provider": provider or entry.get("provider", "gemini"),
            "pages": entry.get("pages", {}),
        }
        headers = {}
        if byok_key:
            headers["X-Provider-Api-Key"] = byok_key
        response = client.post(f"{api_base}/api/audit", json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        predicted_keys = [_issue_key(item) for item in data.get("issues", [])]
        scores = _score(expected_keys, predicted_keys)
        for key in ("tp", "fp", "fn"):
            totals[key] += scores[key]
    totals["precision"] = (
        totals["tp"] / (totals["tp"] + totals["fp"]) if totals["tp"] + totals["fp"] else 0.0
    )
    totals["recall"] = (
        totals["tp"] / (totals["tp"] + totals["fn"]) if totals["tp"] + totals["fn"] else 0.0
    )
    totals["updated_at"] = datetime.utcnow().isoformat()
    return totals


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate audit accuracy.")
    parser.add_argument("--api-base", default="http://localhost:8000")
    parser.add_argument("--byok-key", default=None)
    parser.add_argument("--provider", default=None)
    default_dataset = Path(__file__).resolve().parents[1] / "data" / "eval" / "sample.json"
    parser.add_argument("--dataset", type=Path, default=default_dataset)
    default_output = Path(__file__).resolve().parents[1] / "data" / "eval" / "last_run.json"
    parser.add_argument("--output", type=Path, default=default_output)
    args = parser.parse_args()
    results = evaluate(args.api_base, args.dataset, args.byok_key, args.provider)
    print(json.dumps(results, indent=2))
    try:
        args.output.write_text(json.dumps(results, indent=2), encoding="utf-8")
    except OSError:
        pass


if __name__ == "__main__":
    main()
