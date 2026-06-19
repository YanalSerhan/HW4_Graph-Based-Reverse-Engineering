"""
skill_types.py — Data classes for the SkillRouter.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Skill:
    """A parsed SKILL.md with its metadata and execution body."""

    name: str
    triggers: list[str]
    boundaries: str
    routing_subgraph: str
    execution_body: str
    source_path: Path


@dataclass
class RoutingResult:
    """Result of a SkillRouter.route() call."""

    skill: Skill | None
    confidence: float  # 0.0 – 1.0
    matched_triggers: list[str]
