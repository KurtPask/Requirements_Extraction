from pathlib import Path
import re
import json
from typing import Dict, Any

# Patterns to recognize document types and numbers
DOC_TYPE_PATTERNS = [
    ("OPNAVINST", r"OPNAVINST\s+[\d\.A-Z]+"),
    ("SECNAVINST", r"SECNAVINST\s+[\d\.A-Z]+"),
    ("NAVADMIN", r"NAVADMIN\s+\d+/\d+"),
    ("NTSP", r"NTSP\s+[A-Z0-9\-]+"),
]

# Dates like "14 May 2025" or "20 APR 2018"
DATE_PATTERN = re.compile(
    r"(\d{1,2}\s+(?:[A-Z][a-z]{2}|[A-Z]{3})\s+\d{4})"
)


def extract_metadata_from_text(text: str, file_name: str) -> Dict[str, Any]:
    """
    First-pass metadata extractor based mainly on the first page of the document.
    Fills the 'metadata' part of our JSON schema.
    """
    # Take the first page only for now
    first_page_split = text.split("[PAGE 2]", 1)
    first_page = first_page_split[0]

    doc_type = None
    doc_number = None

    # Try to detect doc_type and doc_number
    for dtype, pattern in DOC_TYPE_PATTERNS:
        m = re.search(pattern, first_page)
        if m:
            doc_type = dtype
            doc_number = m.group(0)
            break

    # Split into non-empty lines
    lines = [l.strip() for l in first_page.splitlines() if l.strip()]

    # --- Title: prefer SUBJ: line, then ALL-CAPS fallback ---
    title = None
    subj_line = next((l for l in lines if l.upper().startswith("SUBJ:")), None)
    if subj_line:
        # Strip "SUBJ:" and leading spaces
        title = subj_line.split(":", 1)[1].strip()
    elif doc_number:
        # Fallback: first ALL-CAPS line after doc_number
        try:
            idx = next(i for i, l in enumerate(lines) if doc_number in l)
            caps_after = [l for l in lines[idx + 1 : idx + 8] if l.isupper() and len(l) > 10]
            if caps_after:
                title = caps_after[0]
        except StopIteration:
            pass

    # --- Issuing organization: "From:" line ---
    issuing_org = None
    from_line = next((l for l in lines if l.upper().startswith("FROM:")), None)
    if from_line:
        issuing_org = from_line.split(":", 1)[1].strip()

    # --- Publication date ---
    date_match = DATE_PATTERN.search(first_page)
    publication_date = date_match.group(1) if date_match else None

    # Build metadata dict matching your schema (subset for now)
    return {
        "doc_id": file_name.replace(".txt", ""),
        "file_name": file_name,
        "file_path": f"parsed_text/{file_name}",
        "source_url": None,

        "doc_type": doc_type,
        "doc_number": doc_number,
        "title": title,
        "issuing_organization": issuing_org,
        "publication_date": publication_date,
        "cancellation_date": None,

        "classification": None,
        "distribution_statement": None,

        "references": [],
        "summary": None,
        "keywords": [],

        "page_count": None,
        "parsing_notes": None,
    }


def batch_extract_metadata(parsed_dir: Path, output_dir: Path) -> None:
    """
    Run metadata extraction on all .txt files in parsed_dir
    and write one *_metadata.json per file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    for txt_file in parsed_dir.glob("*.txt"):
        text = txt_file.read_text(encoding="utf-8")
        meta = extract_metadata_from_text(text, txt_file.name)
        out_path = output_dir / (txt_file.stem + "_metadata.json")
        out_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        print(f"Metadata for {txt_file.name} -> {out_path.name}")


if __name__ == "__main__":
    parsed_dir = Path("parsed_text")
    metadata_dir = Path("metadata")
    batch_extract_metadata(parsed_dir, metadata_dir)
