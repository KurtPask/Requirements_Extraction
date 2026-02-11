import json

from requirements_extraction.validation import validate_jsonl, validate_requirement_record


def test_validate_requirement_record_valid():
    record = {
        "requirement_id": "doc1-s1-r0",
        "source": {"file_name": "doc1.pdf"},
        "subject": {"raw_text": "Commanding officers"},
        "modality_raw": "shall",
        "modality_normalized": "mandatory",
        "action": {"verb": "maintain"},
    }

    assert validate_requirement_record(record) == []


def test_validate_jsonl_reports_errors(tmp_path):
    bad = {
        "requirement_id": "",
        "source": {},
        "subject": {"raw_text": 7},
        "modality_raw": 1,
        "modality_normalized": "mandatory",
        "action": {"verb": 5},
    }

    path = tmp_path / "bad.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(bad) + "\n")

    errors = validate_jsonl(path)
    assert any("requirement_id" in err for err in errors)
    assert any("source.file_name" in err for err in errors)
    assert any("subject.raw_text" in err for err in errors)
    assert any("action.verb" in err for err in errors)
