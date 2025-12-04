# run_requirements_extraction.py

import sys
from pathlib import Path

# Ensure src/ is on the path
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
sys.path.append(str(SRC))

from requirements_extraction.requirements_pipeline import batch_extract_requirements


if __name__ == "__main__":
    parsed_text_dir = "parsed_text"
    metadata_dir = "metadata"
    output_path = "requirements.jsonl"

    batch_extract_requirements(
        parsed_text_dir=parsed_text_dir,
        metadata_dir=metadata_dir,
        output_path=output_path,
    )
