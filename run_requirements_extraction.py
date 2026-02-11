"""CLI entrypoint for batch requirements extraction."""

import argparse

from requirements_extraction.requirements_pipeline import batch_extract_requirements


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch extract requirements to JSONL.")
    parser.add_argument(
        "--parsed-text-dir",
        default="parsed_text",
        help="Directory containing parsed .txt files.",
    )
    parser.add_argument(
        "--metadata-dir",
        default="metadata",
        help="Directory containing *_metadata.json files.",
    )
    parser.add_argument(
        "--output-path",
        default="requirements.jsonl",
        help="Path for output JSONL file.",
    )
    parser.add_argument(
        "--max-candidates",
        type=int,
        default=None,
        help="Optional cap on candidate sentences per file.",
    )
    parser.add_argument(
        "--max-requirements-per-file",
        type=int,
        default=None,
        help="Optional cap on requirements written per file.",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=None,
        help="Optional cap on number of files processed.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    batch_extract_requirements(
        parsed_text_dir=args.parsed_text_dir,
        metadata_dir=args.metadata_dir,
        output_path=args.output_path,
        max_candidates=args.max_candidates,
        max_requirements_per_file=args.max_requirements_per_file,
        max_files=args.max_files,
    )
