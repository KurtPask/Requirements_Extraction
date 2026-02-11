import json

from requirements_extraction.requirements_schema import (
    Requirement,
    RequirementAction,
    RequirementSource,
    RequirementSubject,
)
from requirements_extraction.requirements_pipeline import batch_extract_requirements


def _fake_req(file_name: str, rid: str) -> Requirement:
    return Requirement(
        requirement_id=rid,
        source=RequirementSource(file_name=file_name),
        subject=RequirementSubject(raw_text="Commanding officer"),
        modality_raw="shall",
        modality_normalized="mandatory",
        action=RequirementAction(verb="maintain"),
    )


def test_batch_extract_requirements_writes_output(tmp_path, monkeypatch):
    parsed = tmp_path / "parsed"
    parsed.mkdir()
    metadata = tmp_path / "metadata"
    metadata.mkdir()

    (parsed / "doc1.txt").write_text("shall do x", encoding="utf-8")
    (parsed / "doc2.txt").write_text("shall do y", encoding="utf-8")

    (metadata / "doc1_metadata.json").write_text(
        json.dumps({"file_name": "doc1.pdf", "doc_type": "INST"}), encoding="utf-8"
    )
    (metadata / "doc2_metadata.json").write_text(
        json.dumps({"file_name": "doc2.pdf", "doc_type": "INST"}), encoding="utf-8"
    )

    def fake_extract(text_path, metadata_by_stem, max_candidates=None):
        stem = text_path.split("/")[-1].replace(".txt", "")
        return [_fake_req(f"{stem}.pdf", f"{stem}-r1")]

    monkeypatch.setattr(
        "requirements_extraction.requirements_pipeline.extract_requirements_for_text_file",
        fake_extract,
    )

    output = tmp_path / "requirements.jsonl"
    count = batch_extract_requirements(
        parsed_text_dir=str(parsed),
        metadata_dir=str(metadata),
        output_path=str(output),
    )

    assert count == 2
    lines = output.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2


def test_load_metadata_dir_skips_invalid_and_non_object_files(tmp_path, capsys):
    metadata = tmp_path / "metadata"
    metadata.mkdir()

    (metadata / "bad_metadata.json").write_text("{not json}", encoding="utf-8")
    (metadata / "list_metadata.json").write_text(json.dumps(["invalid"]), encoding="utf-8")
    (metadata / "good_metadata.json").write_text(
        json.dumps({"file_name": "good.pdf", "doc_type": "INST"}), encoding="utf-8"
    )

    from requirements_extraction.requirements_pipeline import load_metadata_dir

    loaded = load_metadata_dir(str(metadata))

    assert "good" in loaded
    assert "bad" not in loaded
    assert "list" not in loaded

    captured = capsys.readouterr()
    assert "Skipping invalid metadata file bad_metadata.json" in captured.out
    assert "Skipping metadata file list_metadata.json" in captured.out


def test_load_metadata_dir_raises_for_missing_directory(tmp_path):
    from requirements_extraction.requirements_pipeline import load_metadata_dir

    missing_dir = tmp_path / "missing"
    try:
        load_metadata_dir(str(missing_dir))
        assert False, "expected FileNotFoundError"
    except FileNotFoundError as exc:
        assert "Metadata directory not found" in str(exc)
