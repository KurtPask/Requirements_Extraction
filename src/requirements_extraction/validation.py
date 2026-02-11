"""Validation helpers for requirements JSONL outputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REQUIRED_TOP_LEVEL_KEYS = {
    "requirement_id",
    "source",
    "subject",
    "modality_raw",
    "modality_normalized",
    "action",
}


def validate_requirement_record(record: dict[str, Any]) -> list[str]:
    """Return a list of validation errors for a single requirement record."""
    errors: list[str] = []

    missing = REQUIRED_TOP_LEVEL_KEYS - set(record.keys())
    for key in sorted(missing):
        errors.append(f"missing key: {key}")

    if not isinstance(record.get("requirement_id"), str) or not record.get("requirement_id", "").strip():
        errors.append("requirement_id must be a non-empty string")

    source = record.get("source")
    if not isinstance(source, dict):
        errors.append("source must be an object")
    else:
        if not isinstance(source.get("file_name"), str) or not source.get("file_name", "").strip():
            errors.append("source.file_name must be a non-empty string")

    subject = record.get("subject")
    if not isinstance(subject, dict):
        errors.append("subject must be an object")
    else:
        if not isinstance(subject.get("raw_text"), str):
            errors.append("subject.raw_text must be a string")

    action = record.get("action")
    if not isinstance(action, dict):
        errors.append("action must be an object")
    else:
        if not isinstance(action.get("verb"), str):
            errors.append("action.verb must be a string")

    if not isinstance(record.get("modality_raw"), str):
        errors.append("modality_raw must be a string")
    if not isinstance(record.get("modality_normalized"), str):
        errors.append("modality_normalized must be a string")

    for list_key in ("applies_to", "topics", "systems_programs", "cross_references"):
        value = record.get(list_key)
        if value is not None and not isinstance(value, list):
            errors.append(f"{list_key} must be a list or null")

    return errors


def validate_jsonl(path: str | Path) -> list[str]:
    """Validate a JSONL file and return error messages with line numbers."""
    path = Path(path)
    errors: list[str] = []

    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"line {line_no}: invalid JSON ({exc})")
                continue

            if not isinstance(record, dict):
                errors.append(f"line {line_no}: record must be a JSON object")
                continue

            record_errors = validate_requirement_record(record)
            errors.extend([f"line {line_no}: {msg}" for msg in record_errors])

    return errors
