# src/requirements_extraction/requirements_candidates.py

import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

# Simple sentence splitter: split on punctuation followed by whitespace + capital/parenthesis
SENTENCE_SPLIT_REGEX = re.compile(r'(?<=[.!?])\s+(?=[A-Z(])')

# We start with a stricter set of modalities to keep token usage low.
# You can add "should" and "may" later if you want more candidates.
RE_REQUIREMENT_MODAL = re.compile(
    r'\b(shall|must|will|is mandatory|are mandatory|'
    r'is required to|are required to|is prohibited|are prohibited)\b',
    flags=re.IGNORECASE
)


@dataclass
class SentenceSpan:
    doc_id: str
    file_name: str
    text: str
    page: Optional[int] = None
    section: Optional[str] = None
    paragraph_index: Optional[int] = None
    sentence_index: Optional[int] = None
    extra_metadata: Optional[Dict[str, Any]] = None


def split_into_sentences(text: str) -> List[str]:
    """
    Very simple sentence splitter.
    You can replace with spaCy / NLTK later if you want better quality.
    """
    text = text.strip()
    if not text:
        return []
    parts = SENTENCE_SPLIT_REGEX.split(text)
    return [p.strip() for p in parts if p.strip()]


def is_requirement_candidate(sentence: str) -> bool:
    """
    Quick heuristic: presence of strong modal / requirement wording.
    """
    return bool(RE_REQUIREMENT_MODAL.search(sentence))


def sentences_to_candidates(
    doc_id: str,
    file_name: str,
    text: str,
    default_page: Optional[int] = None,
    section: Optional[str] = None,
    base_metadata: Optional[Dict[str, Any]] = None,
) -> List[SentenceSpan]:
    """
    Split text into sentences and keep only ones that look like requirements.
    """
    sentences = split_into_sentences(text)
    candidates: List[SentenceSpan] = []

    for idx, s in enumerate(sentences):
        if is_requirement_candidate(s):
            candidates.append(
                SentenceSpan(
                    doc_id=doc_id,
                    file_name=file_name,
                    text=s,
                    page=default_page,
                    section=section,
                    paragraph_index=None,
                    sentence_index=idx,
                    extra_metadata=base_metadata or {},
                )
            )

    return candidates
