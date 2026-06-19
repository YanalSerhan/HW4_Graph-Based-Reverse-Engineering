"""
context_types.py — types for context budget manager.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class FailureMode(str, Enum):
    """Failure modes for context assembly."""

    NONE = "NONE"
    OVERFLOW = "OVERFLOW"
    CONTEXT_ROT = "CONTEXT_ROT"


@dataclass
class AssembledContext:
    """Context package ready to pass to an agent."""

    content: str
    token_estimate: int
    selected_pages: list[str]
    dropped_skills: list[str] = field(default_factory=list)
    was_compacted: bool = False
