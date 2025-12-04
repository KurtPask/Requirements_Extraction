# postprocess_requirements.py

import json
from pathlib import Path
from typing import Optional


def normalize_role_from_subject(raw: Optional[str]) -> Optional[str]:
    """
    Simple deterministic normalization based on subject_raw text.
    No LLMs, just string patterns.
    """
    if not raw:
        return None

    text = raw.strip().lower()

    # Commanding officers / CO
    if text.startswith("commanding officer"):
        return "Commanding Officer"
    if text.startswith("commanding officers"):
        return "Commanding Officer"

    # Type commanders etc. (add more as you see them)
    if text.startswith("type commander"):
        return "Type Commander"

    # The acquiring organization
    if text.startswith("the acquiring organization"):
        return "Acquiring Organization"

    # All NTSPs
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

    # You can keep adding special cases here as you discover patterns.
    return None


def main():
    inp = Path("requirements.jsonl")
    if not inp.exists():
        raise FileNotFoundError("requirements.jsonl not found. Run extraction first.")

    out = Path("requirements_clean.jsonl")

    with inp.open("r", encoding="utf-8") as fin, out.open("w", encoding="utf-8") as fout:
        for line in fin:
            obj = json.loads(line)

            # 1) Normalize subject_normalized_role if we can
            raw_subj = obj.get("subject", {}).get("raw_text")
            new_role = normalize_role_from_subject(raw_subj)
            if new_role is not None:
                obj["subject"]["normalized_role"] = new_role

            # 2) Clean nulls out of applies_to
            applies = obj.get("applies_to")
            if applies:
                obj["applies_to"] = [x for x in applies if x is not None]

            fout.write(json.dumps(obj) + "\n")

    print(f"[INFO] Wrote cleaned requirements to {out}")


if __name__ == "__main__":
    main()
