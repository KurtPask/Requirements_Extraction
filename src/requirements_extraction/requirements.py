from pathlib import Path
import re
import json
from typing import List, Dict, Any, Optional


# ============================================================
#                BASIC SENTENCE & PAGE UTILITIES
# ============================================================

PAGE_MARKER_PATTERN = re.compile(r"\[PAGE\s+(\d+)\]")


def split_into_pages(text: str) -> List[Dict[str, Any]]:
    """
    Split the parsed text (with [PAGE X] markers) into a list of
    {page_number: int, text: str}.
    """
    lines = text.splitlines()
    pages: List[Dict[str, Any]] = []
    current_page_num: Optional[int] = None
    current_lines: List[str] = []

    for line in lines:
        m = PAGE_MARKER_PATTERN.match(line.strip())
        if m:
            # Flush previous page
            if current_page_num is not None:
                pages.append(
                    {"page_number": current_page_num, "text": "\n".join(current_lines)}
                )
            current_page_num = int(m.group(1))
            current_lines = []
        else:
            current_lines.append(line)

    # Flush last page
    if current_page_num is not None and current_lines:
        pages.append(
            {"page_number": current_page_num, "text": "\n".join(current_lines)}
        )

    return pages


SENTENCE_SPLIT_PATTERN = re.compile(
    r"(?<=[\.\?\!])\s+(?=[A-Z0-9\(\[])"  # .,?,! + space + capital/number/(
)


def split_into_sentences(text: str) -> List[str]:
    """
    Simple sentence splitter for instructions/manuals.
    """
    cleaned = re.sub(r"\s+", " ", text)
    parts = SENTENCE_SPLIT_PATTERN.split(cleaned)
    return [p.strip() for p in parts if p.strip()]


# ============================================================
#                REQUIREMENT TRIGGER DETECTION
# ============================================================

TRIGGERS = [
    (re.compile(r"\bshall\b", re.IGNORECASE), "shall"),
    (re.compile(r"\bmust\b", re.IGNORECASE), "must"),
    (re.compile(r"\bare required to\b", re.IGNORECASE), "are required to"),
    (re.compile(r"\bis required to\b", re.IGNORECASE), "is required to"),
    (re.compile(r"\bare to\b", re.IGNORECASE), "are to"),
    (re.compile(r"\bis to\b", re.IGNORECASE), "is to"),
    (re.compile(r"\bwill\b", re.IGNORECASE), "will"),
    (re.compile(r"\bis responsible for\b", re.IGNORECASE), "is responsible for"),
    (re.compile(r"\bare responsible for\b", re.IGNORECASE), "are responsible for"),
]


def find_requirement_triggers(sentence: str) -> List[str]:
    """
    Return a list of trigger phrases that appear in the sentence.
    """
    found = []
    for pattern, label in TRIGGERS:
        if pattern.search(sentence):
            found.append(label)
    return found


def choose_modality(triggers: List[str]) -> Optional[str]:
    """
    Pick a single modality label from the trigger list, biasing toward stronger language.
    Priority order: shall > must > required > are/is to > will > responsible for.
    """
    priority = [
        "shall",
        "must",
        "are required to",
        "is required to",
        "are to",
        "is to",
        "will",
        "are responsible for",
        "is responsible for",
    ]
    for p in priority:
        if p in triggers:
            return p
    return triggers[0] if triggers else None


# ============================================================
#                METADATA LOADING
# ============================================================

def load_metadata_for_doc(stem: str, metadata_dir: Path) -> Dict[str, Any]:
    """
    Load the metadata JSON for a given document stem (e.g. '1500.76E').
    Returns a dict with at least the keys used below; missing file -> minimal defaults.
    """
    meta_path = metadata_dir / f"{stem}_metadata.json"
    if not meta_path.exists():
        return {
            "doc_id": stem,
            "doc_type": None,
            "doc_number": None,
            "title": None,
            "publication_date": None,
        }

    data = json.loads(meta_path.read_text(encoding="utf-8"))
    return {
        "doc_id": data.get("doc_id", stem),
        "doc_type": data.get("doc_type"),
        "doc_number": data.get("doc_number"),
        "title": data.get("title"),
        "publication_date": data.get("publication_date"),
    }


# ============================================================
#             CORE REQUIREMENT EXTRACTION LOGIC
# ============================================================

def extract_requirements_from_text(
    text: str,
    metadata: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Given full text for one document and its metadata, return a list of requirement objects.
    Each requirement is a single sentence matched by one or more trigger phrases.
    """
    pages = split_into_pages(text)
    requirements: List[Dict[str, Any]] = []
    req_counter = 1

    for page in pages:
        page_num = page["page_number"]
        page_text = page["text"]

        sentences = split_into_sentences(page_text)

        for sent in sentences:
            triggers = find_requirement_triggers(sent)
            if not triggers:
                continue  # not a requirement-like sentence

            modality = choose_modality(triggers)

            requirement_id = f"{metadata['doc_id']}-R{req_counter}"
            req_counter += 1

            requirements.append(
                {
                    "requirement_id": requirement_id,
                    "doc_id": metadata["doc_id"],
                    "doc_type": metadata["doc_type"],
                    "doc_number": metadata["doc_number"],
                    "title": metadata["title"],
                    "publication_date": metadata["publication_date"],
                    "page": page_num,
                    "text": sent,
                    "modal_triggers": triggers,
                    "modality": modality,
                }
            )

    return requirements


# ============================================================
#                    BATCH DRIVER
# ============================================================

def batch_extract_requirements(
    parsed_dir: Path,
    metadata_dir: Path,
    output_dir: Path,
) -> None:
    """
    For each .txt in parsed_dir, load its metadata from metadata_dir,
    extract requirements, and write a *_requirements.json file into output_dir.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    for txt_file in parsed_dir.glob("*.txt"):
        stem = txt_file.stem  # e.g. "1500.76E"
        text = txt_file.read_text(encoding="utf-8")
        metadata = load_metadata_for_doc(stem, metadata_dir)

        print(f"Extracting requirements for {txt_file.name} ...")
        reqs = extract_requirements_from_text(text, metadata)

        out_path = output_dir / f"{stem}_requirements.json"
        out_path.write_text(json.dumps(reqs, indent=2), encoding="utf-8")
        print(f"  -> {len(reqs)} requirements written to {out_path.name}")


if __name__ == "__main__":
    parsed_dir = Path("parsed_text")
    metadata_dir = Path("metadata")
    output_dir = Path("requirements")
    batch_extract_requirements(parsed_dir, metadata_dir, output_dir)
