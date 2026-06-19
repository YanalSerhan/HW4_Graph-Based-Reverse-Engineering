"""
bug_types.py — data models for architectural bugs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class BugSeverity(str, Enum):
    """Severity level for a detected architectural bug."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class ArchitecturalBug:
    """A detected structural anti-pattern."""

    bug_type: str
    severity: BugSeverity
    description: str
    affected_node_ids: list[str] = field(default_factory=list)
    recommendation: str = ""
