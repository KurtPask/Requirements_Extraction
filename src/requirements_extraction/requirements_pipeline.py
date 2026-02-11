# src/requirements_extraction/requirements_pipeline.py

import json
from pathlib import Path
from typing import Dict, List, Any, Optional

from .requirements_schema import Requirement, requirement_to_dict
from .requirements_candidates import sentences_to_candidates, SentenceSpan


def load_metadata_dir(metadata_dir: str) -> Dict[str, Dict[str, Any]]:
    metadata_dir_path = Path(metadata_dir)
    if not metadata_dir_path.exists():
        raise FileNotFoundError(f"Metadata directory not found: {metadata_dir_path}")

    meta_index: Dict[str, Dict[str, Any]] = {}

    for path in metadata_dir_path.glob("*_metadata.json"):
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as exc:
            print(f"[WARN] Skipping invalid metadata file {path.name}: {exc}")
            continue

        # Support list-wrapped files
        if isinstance(data, list) and data:
            data = data[0]

        if not isinstance(data, dict):
            print(f"[WARN] Skipping metadata file {path.name}: expected an object.")
            continue

        stem = path.name.replace("_metadata.json", "")

        if "file_name" not in data:
            data["file_name"] = stem + ".pdf"

        meta_index[stem] = data

    return meta_index


def extract_requirements_for_text_file(
    text_path: str,
    metadata_by_stem: Dict[str, Dict[str, Any]],
    max_candidates: Optional[int] = None,
) -> List[Requirement]:
    """
    Extract requirements from a single parsed text file.
    Demo-friendly: cap candidate sentences to keep runtime/cost predictable.
    """
    text_path_obj = Path(text_path)
    file_stem = text_path_obj.stem

    meta = metadata_by_stem.get(file_stem)
    if not meta:
        raise FileNotFoundError(f"No metadata found for doc stem '{file_stem}'")

    file_name = meta.get("file_name", file_stem + ".pdf")

    with text_path_obj.open("r", encoding="utf-8", errors="ignore") as f:
        text = f.read()

    base_meta_for_span = {
        "doc_type": meta.get("doc_type"),
        "title": meta.get("title"),
        "publication_date": meta.get("publication_date"),
        "doc_number": meta.get("doc_number"),
    }

    # STEP 1: candidate sentences
    candidate_spans: List[SentenceSpan] = sentences_to_candidates(
        doc_id=file_stem,
        file_name=file_name,
        text=text,
        default_page=None,
        section=None,
        base_metadata=base_meta_for_span,
    )

    total_found = len(candidate_spans)

    if max_candidates is not None:
        candidate_spans = candidate_spans[:max_candidates]

    print(
        f"[INFO] {file_name}: found {total_found} candidate sentences "
        f"(running {len(candidate_spans)})."
    )

    # STEP 2: LLM extraction
    all_requirements: List[Requirement] = []
    total = len(candidate_spans)

    for i, span in enumerate(candidate_spans, start=1):
        print(f"[INFO] {file_name}: extracting sentence {i}/{total}...")
        try:
            from .requirements_llm import requirements_from_span
            reqs = requirements_from_span(span)
            all_requirements.extend(reqs)
        except Exception as e:
            print(f"[WARN] LLM extraction failed for {file_name} (s={span.sentence_index}): {e}")

    return all_requirements


def extract_one_file_to_jsonl(
    doc_stem: str,
    parsed_text_dir: str,
    metadata_dir: str,
    output_path: str,
    max_candidates: Optional[int] = None,
    max_requirements: Optional[int] = None,
) -> int:
    """
    Extract requirements from EXACTLY ONE document and write JSONL.
    Returns number of requirements written.
    """
    parsed_path = Path(parsed_text_dir) / f"{doc_stem}.txt"
    if not parsed_path.exists():
        raise FileNotFoundError(f"Parsed text not found: {parsed_path}")

    metadata_by_stem = load_metadata_dir(metadata_dir)
    if doc_stem not in metadata_by_stem:
        raise FileNotFoundError(f"Metadata not found: {Path(metadata_dir) / (doc_stem + '_metadata.json')}")

    reqs = extract_requirements_for_text_file(
        text_path=str(parsed_path),
        metadata_by_stem=metadata_by_stem,
        max_candidates=max_candidates,
    )

    if max_requirements is not None:
        reqs = reqs[:max_requirements]

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as out_f:
        for req in reqs:
            out_f.write(json.dumps(requirement_to_dict(req)) + "\n")

    print(f"[INFO] Wrote {len(reqs)} requirements to {out_path}")
    return len(reqs)


def batch_extract_requirements(
    parsed_text_dir: str,
    metadata_dir: str,
    output_path: str,
    max_candidates: Optional[int] = None,
    max_requirements_per_file: Optional[int] = None,
    max_files: Optional[int] = None,
) -> int:
    """
    Extract requirements from all parsed text files and write a single JSONL output.

    Returns the number of requirements written.
    """
    parsed_dir = Path(parsed_text_dir)
    if not parsed_dir.exists():
        raise FileNotFoundError(f"Parsed text directory not found: {parsed_dir}")

    metadata_by_stem = load_metadata_dir(metadata_dir)
    text_files = sorted(parsed_dir.glob("*.txt"))

    if max_files is not None:
        text_files = text_files[:max_files]

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    total_written = 0
    with out_path.open("w", encoding="utf-8") as out_f:
        for text_file in text_files:
            stem = text_file.stem
            if stem not in metadata_by_stem:
                print(f"[WARN] Skipping {text_file.name}: no metadata found.")
                continue

            reqs = extract_requirements_for_text_file(
                text_path=str(text_file),
                metadata_by_stem=metadata_by_stem,
                max_candidates=max_candidates,
            )

            if max_requirements_per_file is not None:
                reqs = reqs[:max_requirements_per_file]

            for req in reqs:
                out_f.write(json.dumps(requirement_to_dict(req)) + "\n")

            total_written += len(reqs)
            print(f"[INFO] {text_file.name}: wrote {len(reqs)} requirements.")

    print(f"[INFO] Wrote {total_written} total requirements to {out_path}")
    return total_written
