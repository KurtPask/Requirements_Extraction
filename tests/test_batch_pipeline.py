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
