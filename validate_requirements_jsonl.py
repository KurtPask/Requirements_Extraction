"""Validate requirements JSONL output format."""

import argparse
import sys

from requirements_extraction.validation import validate_jsonl


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate requirements JSONL output.")
    parser.add_argument("path", help="Path to requirements JSONL file")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    errors = validate_jsonl(args.path)
    if errors:
        for error in errors:
            print(f"[ERROR] {error}")
        sys.exit(1)

    print("[INFO] Validation passed.")
