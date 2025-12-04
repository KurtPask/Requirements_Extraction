# src/requirements_extraction/requirements_schema.py

from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any


@dataclass
class RequirementSource:
    file_name: str
    doc_type: Optional[str] = None
    title: Optional[str] = None
    section: Optional[str] = None
    page: Optional[int] = None
    paragraph_index: Optional[int] = None
    sentence_index: Optional[int] = None


@dataclass
class RequirementSubject:
    raw_text: str
    normalized_role: Optional[str] = None      # e.g., "Commanding Officer", "Sailor"
    echelon: Optional[str] = None              # e.g., "Command", "Type Commander"


@dataclass
class RequirementAction:
    verb: str
    object: Optional[str] = None
    details: Optional[str] = None


@dataclass
class Requirement:
    requirement_id: str
    source: RequirementSource

    subject: RequirementSubject
    modality_raw: str                # raw word/phrase: "shall", "must", "is mandatory"
    modality_normalized: str         # e.g., "mandatory", "recommended", "permitted", "prohibited"

    action: RequirementAction

    condition: Optional[str] = None
    timeframe: Optional[str] = None
    location_scope: Optional[str] = None

    applies_to: Optional[List[str]] = None     # e.g., ["Active Duty", "Reserve"]
    topics: Optional[List[str]] = None         # e.g., ["Harassment Prevention", "GTCC"]
    systems_programs: Optional[List[str]] = None
    cross_references: Optional[List[str]] = None

    extra: Optional[Dict[str, Any]] = None     # escape hatch for anything else


def requirement_to_dict(req: Requirement) -> Dict[str, Any]:
    """Helper to dump a Requirement to a plain dict for JSON serialization."""
    return asdict(req)
