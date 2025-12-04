# query_requirements.py

import json
from pathlib import Path
from typing import List, Dict, Any, Optional


def load_requirements(path: str = "requirements_clean.jsonl") -> List[Dict[str, Any]]:
    """
    Load all requirements from a JSONL file into a list of dicts.
    Defaults to requirements_clean.jsonl (the post-processed file).
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"{path} not found. Make sure you've run extraction and postprocessing."
        )

    reqs: List[Dict[str, Any]] = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            reqs.append(json.loads(line))
    return reqs


def filter_by_system(reqs: List[Dict[str, Any]], keyword: str) -> List[Dict[str, Any]]:
    """
    Filter requirements where systems_programs contains the keyword (case-insensitive).
    Example: keyword="ntsp" or keyword="te".
    """
    keyword = keyword.lower()
    results = []
    for r in reqs:
        systems = r.get("systems_programs") or []
        if any(isinstance(s, str) and keyword in s.lower() for s in systems):
            results.append(r)
    return results


def filter_by_role(reqs: List[Dict[str, Any]], role_keyword: str) -> List[Dict[str, Any]]:
    """
    Filter requirements where subject.normalized_role contains the role_keyword (case-insensitive).
    Example: role_keyword="Acquiring Organization" or "Commanding Officer".
    """
    rk = role_keyword.lower()
    results = []
    for r in reqs:
        subj = r.get("subject", {})
        norm_role: Optional[str] = subj.get("normalized_role")
        if norm_role and rk in norm_role.lower():
            results.append(r)
    return results


def pretty_print_requirements(reqs: List[Dict[str, Any]], limit: int = 10) -> None:
    """
    Print a human-readable view of a few requirements.
    """
    for r in reqs[:limit]:
        src = r["source"]
        subj = r["subject"]
        action = r["action"]

        print(f"ID: {r['requirement_id']}")
        print(f"  Doc: {src['file_name']}")
        print(f"  Subject: {subj['raw_text']} ({subj.get('normalized_role')})")
        print(f"  Modality: {r['modality_raw']} ({r['modality_normalized']})")
        print(f"  Action: {action['verb']} {action.get('object')}")
        if action.get("details"):
            print(f"  Details: {action['details']}")
        if r.get("timeframe"):
            print(f"  Timeframe: {r['timeframe']}")
        if r.get("systems_programs"):
            print(f"  Systems/Programs: {', '.join(r['systems_programs'])}")
        if r.get("topics"):
            print(f"  Topics: {', '.join(r['topics'])}")
        print("-" * 80)


if __name__ == "__main__":
    # Load all cleaned requirements
    all_reqs = load_requirements()

    # 1) Example: show all requirements mentioning NTSP
    print("=== Requirements mentioning NTSP ===")
    ntsp_reqs = filter_by_system(all_reqs, "ntsp")
    print(f"Found {len(ntsp_reqs)} NTSP-related requirements.")
    pretty_print_requirements(ntsp_reqs, limit=5)

    # 2) Example: show all requirements for the Acquiring Organization
    print("\n=== Requirements for Acquiring Organization ===")
    acq_reqs = filter_by_role(all_reqs, "Acquiring Organization")
    print(f"Found {len(acq_reqs)} requirements for Acquiring Organization.")
    pretty_print_requirements(acq_reqs, limit=5)

    # 3)
    print("\n=== Requirements for Commanding Officers ===")
    co_reqs = filter_by_role(all_reqs, "Commanding Officer")
    print(f"Found {len(co_reqs)} requirements for Commanding Officers.")
    pretty_print_requirements(co_reqs, limit=5)
