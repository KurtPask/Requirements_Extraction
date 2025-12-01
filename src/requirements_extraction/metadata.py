from pathlib import Path
import re
import json
from typing import Dict, Any


# ============================================================
#                    DATE PATTERN (MONTH + YEAR)
# ============================================================

MONTH_WORDS = (
    "Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|"
    "January|February|March|April|May|June|July|August|September|October|November|December|"
    "JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|SEPT|OCT|NOV|DEC|"
    "JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER"
)

DATE_PATTERN = re.compile(
    rf"(\b\d{{1,2}}\s+(?:{MONTH_WORDS})\s+\d{{4}}\b|\b(?:{MONTH_WORDS})\s+\d{{4}}\b)"
)


# NAVADMIN-specific 2-digit year (e.g. "SEP 25")
NAVADMIN_DATE_2DIGIT = re.compile(
    r"\b(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s+\d{2}\b"
)


# ============================================================
#                CLASSIFICATION LINE FILTER
# ============================================================

def is_classification_line(line: str) -> bool:
    u = line.upper()
    return (
        u.startswith("CLASSIFICATION")
        or u.startswith("UNCLASSIFIED")
        or u.startswith("CONFIDENTIAL")
        or u.startswith("SECRET")
    )


# ============================================================
#      MULTI-LINE NTSP / TRAINING PLAN TITLES ("FOR THE")
# ============================================================

NTSP_ID_INLINE_PATTERN = re.compile(r"N\d{2}-NTSP-[A-Z0-9\-]+/[A-Z]", re.I)
A_CODE_INLINE_PATTERN = re.compile(r"A-\d{2}-\d{4}[A-Z]?/[A-Z]", re.I)

def extract_multiline_title_with_for_the(lines):

    idx = None
    for i, line in enumerate(lines):
        if "FOR THE" in line.upper():
            idx = i
            break

    if idx is None:
        return None

    window = []
    start = max(0, idx - 2)
    end = min(len(lines), idx + 3)

    for j in range(start, end):
        l = lines[j].strip()
        if not l:
            continue

        u = l.upper()

        if u.startswith("[PAGE"):
            continue
        if NTSP_ID_INLINE_PATTERN.search(u) or A_CODE_INLINE_PATTERN.search(u):
            continue

        if any(c.isalpha() for c in l) and u == u.upper() and len(l) > 3:
            window.append(l)

    if window:
        return " ".join(window)

    return None


# ============================================================
#                  NAVADMIN DETECTION (TOP)
# ============================================================

NAVADMIN_PATTERN = re.compile(r"NAVADMIN\s+\d+/\d{2}", re.I)

def extract_navadmin(text: str, file_name: str):
    """Extract NAVADMIN doc_number, title (SUBJ/ multi-line), and date (e.g. SEP 25)."""
    first_page = text.split("[PAGE 2]", 1)[0]
    raw_lines = [l.strip() for l in first_page.splitlines() if l.strip()]

    m = NAVADMIN_PATTERN.search(first_page)
    if not m:
        return None

    doc_number = m.group(0)
    doc_type = "NAVADMIN"

    title = None
    subj_idx = None
    for i, l in enumerate(raw_lines):
        if l.upper().startswith("SUBJ/"):
            subj_idx = i
            break

    if subj_idx is not None:
        parts = []
        first = raw_lines[subj_idx]
        parts.append(first.split("/", 1)[1].strip(" /"))

        for j in range(subj_idx + 1, min(subj_idx + 5, len(raw_lines))):
            nxt = raw_lines[j].strip()
            up = nxt.upper()
            if not nxt:
                break
            if up.startswith("REF/") or up.startswith("RMKS/") or up.startswith("MSGID/"):
                break
            if is_classification_line(nxt):
                continue
            parts.append(nxt.strip(" /"))

        title = " ".join(parts) if parts else None

    publication_date = None
    two_d = NAVADMIN_DATE_2DIGIT.search(first_page)
    if two_d:
        publication_date = two_d.group(0)
    else:
        dm = DATE_PATTERN.search(first_page)
        if dm:
            publication_date = dm.group(1)

    return {
        "doc_id": file_name.replace(".txt", ""),
        "doc_type": doc_type,
        "doc_number": doc_number,
        "title": title,
        "publication_date": publication_date,
    }


# ============================================================
#         OPNAVINST / SECNAVINST / NTSP (SECOND PRIORITY)
# ============================================================

NAVY_DOC_PATTERNS = [
    ("SECNAVINST", r"SECNAVINST\s+[\d\.A-Z/]+"),
    ("OPNAVINST", r"OPNAVINST\s+[\d\.A-Z/]+"),
    ("NTSP", r"NTSP\s+[A-Z0-9\-]+"),
]

def extract_navy_instruction(text: str, file_name: str):
    """Extract metadata for OPNAVINST, SECNAVINST, NTSP that look like instructions."""
    first_page = text.split("[PAGE 2]", 1)[0]
    raw_lines = [l.strip() for l in first_page.splitlines() if l.strip()]
    lines = [l for l in raw_lines if not is_classification_line(l)]

    doc_type = None
    doc_number = None

    for dtype, pattern in NAVY_DOC_PATTERNS:
        m = re.search(pattern, first_page)
        if m:
            doc_type = dtype
            doc_number = m.group(0)
            break

    if not doc_number:
        return None

    title = None
    subj_line = next((l for l in lines if l.upper().startswith("SUBJ:")), None)
    if subj_line:
        title = subj_line.split(":", 1)[1].strip()

    if not title:
        title = extract_multiline_title_with_for_the(lines)

    if not title:
        caps = [
            l for l in lines
            if l.isupper() and len(l) > 5 and doc_number not in l
        ]
        if caps:
            title = caps[0]

    # Date
    publication_date = None
    dm = DATE_PATTERN.search(first_page)
    if dm:
        publication_date = dm.group(1)

    return {
        "doc_id": file_name.replace(".txt", ""),
        "doc_type": doc_type,
        "doc_number": doc_number,
        "title": title,
        "publication_date": publication_date,
    }


# ============================================================
#             TECH MANUALS / NTSP TRAINING DOCS
# ============================================================

NTSP_ID_PATTERN = re.compile(r"\bN\d{2}-NTSP-[A-Z0-9\-]+/[A-Z]\b", re.I)
A_CODE_PATTERN = re.compile(r"\bA-\d{2}-\d{4}[A-Z]?/[A-Z]\b", re.I)

TECH_DOC_PATTERNS = [
    ("AIM", r"AIM[-\s]?\d+[A-Z]?"),
    ("NAVAIR", r"NAVAIR\s+[\dA-Z\-]+"),
    ("TECH_MANUAL", r"(TECHNICAL\s+MANUAL|TECH\s+MANUAL|TM\s+\d[\d\-A-Z]+)"),
]

def extract_technical_manual(text: str, file_name: str):
    """Extract metadata for AIM-9M training plan, MORIAH, SFTP, NAVAIR manuals, etc."""
    first_page = text.split("[PAGE 2]", 1)[0]
    raw_lines = [l.strip() for l in first_page.splitlines() if l.strip()]
    lines = [l for l in raw_lines if not is_classification_line(l)]

    doc_type = None
    doc_number = None

    ntsp_match = NTSP_ID_PATTERN.search(first_page)
    if ntsp_match:
        doc_number = ntsp_match.group(0)
        doc_type = "NTSP"
    else:
        a_match = A_CODE_PATTERN.search(first_page)
        if a_match:
            doc_number = a_match.group(0)
            doc_type = "NTSP"
        else:
            for dtype, pattern in TECH_DOC_PATTERNS:
                m = re.search(pattern, first_page, re.I)
                if m:
                    doc_type = dtype
                    doc_number = m.group(0).strip()
                    break

    if not doc_number:
        return None

    title = extract_multiline_title_with_for_the(lines)

    if not title:
        caps = [l for l in lines if l.isupper() and len(l) > 5]
        if caps:
            title = " ".join(caps[:2])

    publication_date = None
    dm = DATE_PATTERN.search(first_page)
    if dm:
        publication_date = dm.group(1)

    doc_id = doc_number

    return {
        "doc_id": doc_id,
        "doc_type": doc_type,
        "doc_number": doc_number,
        "title": title,
        "publication_date": publication_date,
    }


# ============================================================
#                   GENERIC FALLBACK
# ============================================================

def extract_generic(text: str, file_name: str):
    first_page = text.split("[PAGE 2]", 1)[0]
    raw = [l.strip() for l in first_page.splitlines() if l.strip()]
    lines = [l for l in raw if not is_classification_line(l)]

    title = extract_multiline_title_with_for_the(lines)

    if not title:
        for l in lines:
            if any(c.isalpha() for c in l) and len(l) > 5:
                title = l
                break

    publication_date = None
    dm = DATE_PATTERN.search(first_page)
    if dm:
        publication_date = dm.group(1)
    else:
        year_m = re.search(r"(19|20)\d{2}", first_page)
        if year_m:
            publication_date = year_m.group(0)

    return {
        "doc_id": file_name.replace(".txt", ""),
        "doc_type": "UNKNOWN",
        "doc_number": None,
        "title": title,
        "publication_date": publication_date,
    }


# ============================================================
#              MASTER METADATA DISPATCHER
# ============================================================

def extract_metadata_from_text(text: str, file_name: str) -> Dict[str, Any]:
    # 1. NAVADMIN
    navadmin = extract_navadmin(text, file_name)
    if navadmin:
        return navadmin

    # 2. OPNAVINST / SECNAVINST / NTSP instructions
    navy = extract_navy_instruction(text, file_name)
    if navy:
        return navy

    # 3. Technical manuals, NTSP training plans, NAVAIR, AIM-9, etc.
    tech = extract_technical_manual(text, file_name)
    if tech:
        return tech

    # 4. Generic fallback
    return extract_generic(text, file_name)


# ============================================================
#                    BATCH DRIVER
# ============================================================

def batch_extract_metadata(parsed_dir: Path, output_dir: Path) -> None:
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
