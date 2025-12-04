# src/requirements_extraction/requirements_pipeline.py

import json
from pathlib import Path
from typing import Dict, List, Any

from .requirements_schema import Requirement, requirement_to_dict
from .requirements_candidates import sentences_to_candidates, SentenceSpan
from .requirements_llm import requirements_from_span


def load_metadata_dir(metadata_dir: str) -> Dict[str, Dict[str, Any]]:
    """
    Load all *_metadata.json files and index by document stem (e.g. '1500.76E').
    """
    metadata_dir_path = Path(metadata_dir)
    meta_index: Dict[str, Dict[str, Any]] = {}

    for path in metadata_dir_path.glob("*_metadata.json"):
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # Support single-object files or list-wrapped files
        if isinstance(data, list):
            if len(data) == 0:
                continue
            data = data[0]

        if not isinstance(data, dict):
            continue

        stem = path.name.replace("_metadata.json", "")

        if "file_name" not in data:
            data["file_name"] = stem + ".pdf"

        meta_index[stem] = data

    return meta_index


def extract_requirements_for_text_file(
    text_path: str,
    metadata_by_stem: Dict[str, Dict[str, Any]],
) -> List[Requirement]:
    """
    Extract requirements from a single parsed text file.
    """
    text_path_obj = Path(text_path)
    file_stem = text_path_obj.stem  # e.g. "1500.76E"

    meta = metadata_by_stem.get(file_stem, {"file_name": file_stem + ".pdf"})
    file_name = meta.get("file_name", file_stem + ".pdf")

    # Load the text
    with text_path_obj.open("r", encoding="utf-8", errors="ignore") as f:
        text = f.read()

    # Base metadata that will be passed into each SentenceSpan
    base_meta_for_span = {
        "doc_type": meta.get("doc_type"),
        "title": meta.get("title"),
    }

    # --- STEP 1: Find requirement-like sentences -------------------------
    candidate_spans: List[SentenceSpan] = sentences_to_candidates(
        doc_id=file_stem,
        file_name=file_name,
        text=text,
        default_page=None,
        section=None,
        base_metadata=base_meta_for_span,
    )

    # TEMP CAP for debugging + cost control
    #MAX_CANDIDATES = 25  # <--- change to None or remove when ready
    #candidate_spans = candidate_spans[:MAX_CANDIDATES]

    total = len(candidate_spans)
    print(f"[INFO] {file_name}: found {total} candidate requirement sentences.")

    # --- STEP 2: Extract structured requirements --------------------------
    all_requirements: List[Requirement] = []

    for i, span in enumerate(candidate_spans, start=1):
        print(f"[INFO] {file_name}: extracting sentence {i}/{total}...")

        try:
            reqs = requirements_from_span(span)
            all_requirements.extend(reqs)
        except Exception as e:
            print(
                f"[WARN] LLM extraction failed for {file_name} "
                f"(sentence index {span.sentence_index}): {e}"
            )

    return all_requirements


def batch_extract_requirements(
    parsed_text_dir: str,
    metadata_dir: str,
    output_path: str,
) -> None:
    """
    Main batch entrypoint.

    Processes ALL .txt files in parsed_text_dir and writes all requirements
    into a single JSONL file (one requirement per line).
    """
    metadata_by_stem = load_metadata_dir(metadata_dir)

    parsed_text_dir_path = Path(parsed_text_dir)
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    text_files = sorted(parsed_text_dir_path.glob("*.txt"))
    print(f"[INFO] Found {len(text_files)} parsed text files.")

    # Overwrite any existing requirements.jsonl
    with out_path.open("w", encoding="utf-8") as out_f:
        for text_path in text_files:
            print(f"[INFO] Processing {text_path} ...")

            reqs = extract_requirements_for_text_file(
                text_path=str(text_path),
                metadata_by_stem=metadata_by_stem,
            )

            for req in reqs:
                out_f.write(json.dumps(requirement_to_dict(req)) + "\n")

    print(f"[INFO] Done. Wrote requirements to {out_path}")

