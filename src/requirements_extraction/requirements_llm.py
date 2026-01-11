# src/requirements_extraction/requirements_llm.py

from dotenv import load_dotenv
import os
import json
import re
from typing import List, Dict, Any

load_dotenv()

from openai import OpenAI

from .requirements_schema import (
    Requirement,
    RequirementSource,
    RequirementSubject,
    RequirementAction,
)
from .requirements_candidates import SentenceSpan

client = OpenAI(api_key=os.getenv("OPEN_API_KEY"))

# --- Modality configuration --- #

MODALITY_MAP = {
    "shall": "mandatory",
    "must": "mandatory",
    "will": "mandatory",
    "is mandatory": "mandatory",
    "are mandatory": "mandatory",
    "is required to": "mandatory",
    "are required to": "mandatory",
    "should": "recommended",
    "may": "permitted",
    "is prohibited": "prohibited",
    "are prohibited": "prohibited",
}


def normalize_modality(modality_raw: str) -> str:
    mr = modality_raw.lower().strip()
    for k, v in MODALITY_MAP.items():
        if k in mr:
            return v
    if "prohibit" in mr:
        return "prohibited"
    return "unknown"


# --- Prompt building --- #

def build_llm_prompt(span: SentenceSpan) -> str:
    """
    Build the instruction for the LLM. We keep it JSON-first and
    tightly specify the schema.
    """
    instruction = """
You are extracting structured REQUIREMENTS from U.S. Navy policy documents.

Given the TEXT below, identify any distinct requirements.

A requirement is a statement that describes something that a person or role MUST, SHALL, SHOULD, WILL, MAY, or IS PROHIBITED from doing.

Return ONLY valid JSON in the following form:

[
  {
    "subject_raw": "...",
    "subject_normalized_role": "...",
    "modality_raw": "...",
    "action_verb": "...",
    "action_object": "...",
    "action_details": "...",
    "condition": "...",
    "timeframe": "...",
    "location_scope": "...",
    "applies_to": ["..."],
    "topics": ["..."],
    "systems_programs": ["..."],
    "cross_references": ["..."],
    "extra": {}
  }
]

Guidelines:
- Use "subject_raw" for the exact wording of who has the requirement (e.g., "Commanding officers", "All hands").
- "subject_normalized_role" should be a simplified role when obvious (e.g., "Commanding Officer", "Sailor", "Type Commander").
- If the text does NOT clearly specify a person or role (for example, if the subject is a document, estimate, plan, or acronym like "TE"), then set "subject_normalized_role" to null and do NOT guess.
- Do NOT invent a job title or organization that is not explicitly stated in the text.
- "modality_raw" must be the exact word or phrase expressing obligation ("shall", "must", "will", "should", "may", "is prohibited", etc.).
- "action_verb" should be the main verb of the required action (e.g., "maintain", "establish", "ensure").
- "action_object" should be the direct object of that verb (e.g., "a CMEO program", "training records").
- "action_details" can include any important extra detail about how/when the action is done.
- If something is not stated, use null (not an empty string).
- If there is NO requirement in the text, return [].

Do not include comments or any other text outside the JSON array.

TEXT:
"""
    return instruction + "\n" + span.text


# --- OpenAI call --- #

def call_llm(prompt: str) -> str:
    """
    Call the OpenAI Chat Completions API to get structured requirements JSON.
    """
    response = client.chat.completions.create(
        model="gpt-4.1-mini",  # cheap and good for this task
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert at extracting structured requirements "
                    "from U.S. Navy policy documents and instructions."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0,
    )
    return response.choices[0].message.content




# --- JSON parsing and conversion to Requirement objects --- #

def parse_llm_json(raw_json: str) -> List[Dict[str, Any]]:
    """
    Safely load the JSON returned by the LLM. Attempt to repair minor formatting issues.
    """
    raw_json = raw_json.strip()

    # Sometimes models wrap code fences, strip if present
    if raw_json.startswith("```"):
        raw_json = re.sub(r"^```[a-zA-Z0-9]*", "", raw_json)
        raw_json = re.sub(r"```$", "", raw_json).strip()

    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", raw_json, flags=re.DOTALL)
        if not match:
            return []
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return []

    if not isinstance(data, list):
        return []
    return data


def build_requirement_id(source: RequirementSource, idx_in_span: int) -> str:
    """
    Build a semi-stable requirement ID using doc info and indices.
    """
    base = source.file_name.replace(".pdf", "").replace(" ", "_")
    parts = [base]

    if source.page is not None:
        parts.append(f"p{source.page}")
    if source.paragraph_index is not None:
        parts.append(f"par{source.paragraph_index}")
    if source.sentence_index is not None:
        parts.append(f"s{source.sentence_index}")
    parts.append(f"r{idx_in_span}")

    return "-".join(parts)


def requirements_from_span(span: SentenceSpan) -> List[Requirement]:
    """
    Main function: given a candidate sentence span, call the LLM and
    convert its JSON response into a list of Requirement objects.
    """
    prompt = build_llm_prompt(span)
    raw = call_llm(prompt)
    parsed = parse_llm_json(raw)

    requirements: List[Requirement] = []

    source = RequirementSource(
        file_name=span.file_name,
        doc_type=span.extra_metadata.get("doc_type") if span.extra_metadata else None,
        title=span.extra_metadata.get("title") if span.extra_metadata else None,
        section=span.section,
        page=span.page,
        paragraph_index=span.paragraph_index,
        sentence_index=span.sentence_index,
    )

    for idx, item in enumerate(parsed):
        subject_raw = (item.get("subject_raw") or "").strip()
        subject_norm = item.get("subject_normalized_role") or None

        modality_raw = (item.get("modality_raw") or "").strip() or "UNKNOWN"
        modality_normalized = normalize_modality(modality_raw)

        action_verb = (item.get("action_verb") or "").strip()
        action_obj = item.get("action_object") or None
        action_details = item.get("action_details") or None

        req = Requirement(
            requirement_id=build_requirement_id(source, idx_in_span=idx),
            source=source,
            subject=RequirementSubject(
                raw_text=subject_raw,
                normalized_role=subject_norm,
                echelon=None,  # optional field you can fill later
            ),
            modality_raw=modality_raw,
            modality_normalized=modality_normalized,
            action=RequirementAction(
                verb=action_verb,
                object=action_obj,
                details=action_details,
            ),
            condition=item.get("condition") or None,
            timeframe=item.get("timeframe") or None,
            location_scope=item.get("location_scope") or None,
            applies_to=item.get("applies_to") or None,
            topics=item.get("topics") or None,
            systems_programs=item.get("systems_programs") or None,
            cross_references=item.get("cross_references") or None,
            extra=item.get("extra") or None,
        )

        requirements.append(req)

    return requirements
