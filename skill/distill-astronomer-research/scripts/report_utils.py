"""Shared helpers for reading and writing distiller JSON reports."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def records_from_payload(payload: Any) -> list[dict]:
    if payload is None:
        return []
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        records = payload.get("records", [])
        if isinstance(records, list):
            return records
    raise ValueError("Expected a report list or an object with a records list")


def load_records(path: Path, default: Any = None) -> list[dict]:
    return records_from_payload(load_json(path, default if default is not None else []))


def count_by(records: list[dict], key: str) -> dict[str, int]:
    return dict(Counter(str(item.get(key, "unknown")) for item in records))


def write_report(path: Path, records: list[dict], summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"summary": summary, "records": records}
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
