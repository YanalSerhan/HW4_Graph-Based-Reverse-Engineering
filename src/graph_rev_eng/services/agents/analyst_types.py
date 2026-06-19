"""
analyst_types.py — data models for graph analyst.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ArchitecturalInsight:
    """A single architectural finding produced by the GraphAnalystAgent."""

    title: str
    observation: str
    relation: str
    confidence_level: str  # EXTRACTED | INFERRED | AMBIGUOUS
    context: str
    source_node_ids: list[str]
    raw_evidence: str = ""
