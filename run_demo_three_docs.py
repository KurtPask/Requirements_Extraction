# run_demo_three_docs.py

import sys
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
sys.path.append(str(SRC))

from requirements_extraction.requirements_pipeline import extract_one_file_to_jsonl


# -----------------------
# DEMO CONFIG (LOCKED)
# -----------------------
DOC_STEMS = [
    "aim-9m",
    "NAV25210",
    "1500.76E",
]

PARSED_TEXT_DIR = "parsed_text"
METADATA_DIR = "metadata"

MAX_REQUIREMENTS_PER_DOC = 15

# This controls runtime/cost: candidate sentences => LLM calls.
# Keep it moderate; you can tune up/down.
MAX_CANDIDATES_PER_DOC = 40

DEMO_OUT_DIR = Path("demo_outputs")
DEMO_OUT_DIR.mkdir(parents=True, exist_ok=True)

COMBINED_RAW = Path("requirements.jsonl")
COMBINED_CLEAN = Path("requirements_clean.jsonl")


def run_postprocess(inp_path: Path, out_path: Path):
    subprocess.check_call([
        sys.executable,
        "postprocess_requirements.py",
        "--inp", str(inp_path),
        "--out", str(out_path),
    ])


def merge_jsonl(inputs, output_path: Path):
    with output_path.open("w", encoding="utf-8") as out_f:
        for p in inputs:
            with Path(p).open("r", encoding="utf-8") as in_f:
                for line in in_f:
                    out_f.write(line)


def main():
    print("\n========================================")
    print(" DEMO: Three-Document Requirements Run ")
    print("  (aim-9m, NAV25210, 1500.76E)")
    print("========================================\n")

    per_doc_raw = []
    per_doc_clean = []

    for stem in DOC_STEMS:
        # sanity checks early
        txt_path = Path(PARSED_TEXT_DIR) / f"{stem}.txt"
        meta_path = Path(METADATA_DIR) / f"{stem}_metadata.json"

        if not txt_path.exists():
            raise FileNotFoundError(f"Missing parsed text: {txt_path}")
        if not meta_path.exists():
            raise FileNotFoundError(f"Missing metadata: {meta_path}")

        raw_path = DEMO_OUT_DIR / f"{stem}_requirements.jsonl"
        clean_path = DEMO_OUT_DIR / f"{stem}_requirements_clean.jsonl"

        print(f"\n--- Extracting from: {stem} ---")
        extract_one_file_to_jsonl(
            doc_stem=stem,
            parsed_text_dir=PARSED_TEXT_DIR,
            metadata_dir=METADATA_DIR,
            output_path=str(raw_path),
            max_candidates=MAX_CANDIDATES_PER_DOC,
            max_requirements=MAX_REQUIREMENTS_PER_DOC,
        )

        run_postprocess(raw_path, clean_path)

        per_doc_raw.append(raw_path)
        per_doc_clean.append(clean_path)

    # Merge into filenames expected by your app/query scripts
    merge_jsonl(per_doc_raw, COMBINED_RAW)
    merge_jsonl(per_doc_clean, COMBINED_CLEAN)

    print("\n[DEMO OUTPUTS]")
    print("  - Per-doc raw JSONL:    demo_outputs/<stem>_requirements.jsonl")
    print("  - Per-doc clean JSONL:  demo_outputs/<stem>_requirements_clean.jsonl")
    print(f"  - Combined raw JSONL:   {COMBINED_RAW}")
    print(f"  - Combined clean JSONL: {COMBINED_CLEAN}")
    print("\n[DEMO COMPLETE]\n")

    print("Next:")
    print("  • Open the app: streamlit run app.py")
    print("  • Or query CLI: python query_requirements.py")


if __name__ == "__main__":
    main()
