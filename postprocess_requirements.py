# postprocess_requirements.py

import json
from pathlib import Path
from typing import Optional
import argparse


def normalize_role_from_subject(raw: Optional[str]) -> Optional[str]:
    """
    Deterministic normalization based on subject_raw text (no LLM).
    """
    if not raw:
        return None

    text = raw.strip().lower()

    if text.startswith("commanding officer"):
        return "Commanding Officer"
    if text.startswith("commanding officers"):
        return "Commanding Officer"
    if text.startswith("type commander"):
        return "Type Commander"
    if text.startswith("the acquiring organization"):
        return "Acquiring Organization"
    if text.startswith("all ntsps"):
        return "NTSP (Document)"
    if text.startswith("all ntsp"):
        return "NTSP (Document)"
    if text.startswith("commanders"):
        return "Commander"
    if text.startswith("program managers"):
        return "Program Manager"
    if text.startswith("fleet commanders"):
        return "Fleet Commander"

    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inp", default="requirements.jsonl", help="Input JSONL (default: requirements.jsonl)")
    ap.add_argument("--out", default="requirements_clean.jsonl", help="Output JSONL (default: requirements_clean.jsonl)")
    args = ap.parse_args()

    inp = Path(args.inp)
    if not inp.exists():
        raise FileNotFoundError(f"{inp} not found. Run extraction first.")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    with inp.open("r", encoding="utf-8") as fin, out.open("w", encoding="utf-8") as fout:
        for line in fin:
            obj = json.loads(line)

            raw_subj = obj.get("subject", {}).get("raw_text")
            new_role = normalize_role_from_subject(raw_subj)
            if new_role is not None and isinstance(obj.get("subject"), dict):
                obj["subject"]["normalized_role"] = new_role

            applies = obj.get("applies_to")
            if applies:
                obj["applies_to"] = [x for x in applies if x is not None]

            fout.write(json.dumps(obj) + "\n")

    print(f"[INFO] Wrote cleaned requirements to {out}")


if __name__ == "__main__":
    main()
