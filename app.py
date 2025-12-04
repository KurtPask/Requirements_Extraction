# app.py
#
# Simple UI for exploring requirements_clean.jsonl using Streamlit.

import json
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import streamlit as st


@st.cache_data
def load_requirements(path: str = "requirements_clean.jsonl") -> List[Dict[str, Any]]:
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

def build_sentence(
    subject_raw: str | None,
    modality_raw: str | None,
    verb: str | None,
    obj: str | None,
    details: str | None,
    timeframe: str | None,
) -> str:
    """
    Build a human-readable sentence from the structured fields.
    Does NOT call any LLM; just templates the pieces together.
    De-duplicates repeated details/timeframe text.
    """
    subject = (subject_raw or "").strip()
    modality = (modality_raw or "").strip().lower()
    v = (verb or "").strip()
    o = (obj or "").strip()
    det = (details or "").strip()
    tf = (timeframe or "").strip()

    # Normalize modality a bit
    if modality in {"shall", "must"}:
        modal_word = "must"
    elif modality == "should":
        modal_word = "should"
    elif modality == "will":
        modal_word = "will"
    else:
        # If we don't recognize it, just skip modality
        modal_word = ""

    # Start building the core clause
    parts = []

    if subject:
        # Capitalize first letter if needed
        subject = subject[0].upper() + subject[1:]
        parts.append(subject)
    else:
        parts.append("This requirement")

    # Modality + verb
    if modal_word and v:
        parts.append(f"{modal_word} {v}")
    elif v:
        parts.append(v)
    elif modal_word:
        parts.append(modal_word)

    # Object
    if o:
        parts.append(o)

    sentence = " ".join(parts)

    # --- Trailing clauses (details + timeframe) with de-duplication ---
    trailing_raw = []
    if det:
        trailing_raw.append(det)
    if tf:
        trailing_raw.append(tf)

    # Deduplicate by normalized text
    seen = set()
    trailing_unique: list[str] = []
    for t in trailing_raw:
        key = t.strip(" .,").lower()
        if key and key not in seen:
            seen.add(key)
            trailing_unique.append(t)

    if trailing_unique:
        sentence = sentence.rstrip(", ")
        sentence += ", " + ", ".join(trailing_unique)

    # Ensure it ends with a period
    sentence = sentence.strip()
    if sentence and not sentence.endswith((".", "!", "?")):
        sentence += "."

    return sentence


def to_dataframe(reqs: List[Dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for r in reqs:
        src = r.get("source", {})
        subj = r.get("subject", {})
        action = r.get("action", {})

        # Safely handle None values
        systems_raw = r.get("systems_programs") or []
        topics_raw = r.get("topics") or []

        systems = [s for s in systems_raw if isinstance(s, str)]
        topics = [t for t in topics_raw if isinstance(t, str)]

        subject_raw = subj.get("raw_text")
        subject_role = subj.get("normalized_role")
        modality_raw = r.get("modality_raw")
        modality_norm = r.get("modality_normalized")
        verb = action.get("verb")
        obj = action.get("object")
        details = action.get("details")
        timeframe = r.get("timeframe")

        human_sentence = build_sentence(
            subject_raw=subject_raw,
            modality_raw=modality_raw,
            verb=verb,
            obj=obj,
            details=details,
            timeframe=timeframe,
        )

        rows.append(
            {
                "requirement_id": r.get("requirement_id"),
                "file_name": src.get("file_name"),
                "doc_type": src.get("doc_type"),
                "title": src.get("title"),
                "subject_raw": subject_raw,
                "subject_role": subject_role,
                "modality_raw": modality_raw,
                "modality": modality_norm,
                "verb": verb,
                "object": obj,
                "details": details,
                "timeframe": timeframe,
                "systems_programs": ", ".join(systems),
                "topics": ", ".join(topics),
                "sentence": human_sentence,
            }
        )
    df = pd.DataFrame(rows)
    return df

def main():
    st.set_page_config(page_title="Requirements Explorer", layout="wide")
    st.title("Navy Requirements Explorer")

    st.write(
        "This app is reading from **requirements_clean.jsonl** "
        "(currently from OPNAVINST 1500.76E). "
        "The same UI will work once more documents are added."
    )

    # Load data
    reqs = load_requirements()
    df = to_dataframe(reqs)

    # Sidebar filters
    st.sidebar.header("Filters")

    # Document type filter
    doc_types = sorted([dt for dt in df["doc_type"].dropna().unique()])
    doc_type_choice = st.sidebar.selectbox(
        "Document type", ["Any"] + doc_types
    )

    # Subject role filter
    roles = sorted([r for r in df["subject_role"].dropna().unique()])
    role_choice = st.sidebar.selectbox(
        "Subject role", ["Any"] + roles
    )

    # Modality filter (mandatory / recommended / optional / etc.)
    modalities = sorted([m for m in df["modality"].dropna().unique()])
    modality_choice = st.sidebar.multiselect(
        "Modality (normalized)", modalities, default=modalities
    )

    # Keyword search (search across subject, object, details, topics, systems)
    keyword = st.sidebar.text_input(
        "Keyword search (subject, action, topics, systems)", ""
    ).strip()

    # Apply filters
    filtered = df.copy()

    if doc_type_choice != "Any":
        filtered = filtered[filtered["doc_type"] == doc_type_choice]

    if role_choice != "Any":
        filtered = filtered[filtered["subject_role"] == role_choice]

    if modality_choice:
        filtered = filtered[filtered["modality"].isin(modality_choice)]

    if keyword:
        kw = keyword.lower()

        def match_row(row) -> bool:
            fields = [
                str(row.get("subject_raw") or ""),
                str(row.get("object") or ""),
                str(row.get("details") or ""),
                str(row.get("topics") or ""),
                str(row.get("systems_programs") or ""),
            ]
            combined = " ".join(fields).lower()
            return kw in combined

        filtered = filtered[filtered.apply(match_row, axis=1)]

    st.subheader(f"Matching requirements: {len(filtered)}")

    # Show table
    st.dataframe(
        filtered[
            [
                "requirement_id",
                "doc_type",
                "file_name",
                "sentence",
                "subject_raw",
                "subject_role",
                "modality",
                "verb",
                "object",
                "timeframe",
                "systems_programs",
                "topics",
            ]
        ],
        use_container_width=True,
        height=500,
    )

    # Optional: show details for a selected requirement
    st.markdown("---")
    st.subheader("Requirement details")

    selected_id = st.selectbox(
        "Select a requirement_id to inspect",
        ["(none)"] + list(filtered["requirement_id"].unique()),
    )

    if selected_id != "(none)":
        req_row = filtered[filtered["requirement_id"] == selected_id].iloc[0]
        st.write("**Requirement ID:**", req_row["requirement_id"])
        st.write("**Document:**", req_row["file_name"])
        st.write("**Doc type:**", req_row["doc_type"])
        st.write("**Title:**", req_row["title"])

        st.write("**Sentence:**", req_row["sentence"])

        st.write("**Subject:**", req_row["subject_raw"], f"({req_row['subject_role']})")
        st.write("**Modality:**", req_row["modality_raw"], f"({req_row['modality']})")
        st.write("**Action:**", f"{req_row['verb']} {req_row['object']}")
        if req_row["details"]:
            st.write("**Details:**", req_row["details"])
        if req_row["timeframe"]:
            st.write("**Timeframe:**", req_row["timeframe"])
        if req_row["systems_programs"]:
            st.write("**Systems/Programs:**", req_row["systems_programs"])
        if req_row["topics"]:
            st.write("**Topics:**", req_row["topics"])


if __name__ == "__main__":
    main()
