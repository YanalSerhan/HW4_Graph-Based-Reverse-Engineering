"""
inspector_helpers.py — source code reading and validation helper methods.
"""

from __future__ import annotations

import ast
import logging
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from ...constants import EDGE_TYPE_AMBIGUOUS

if TYPE_CHECKING:
    from pathlib import Path

    from ..graph_models import Graph, GraphEdge
    from .graph_analyst import ArchitecturalInsight

logger = logging.getLogger(__name__)


class ValidationOutcome(str, Enum):
    """Result of validating an insight against source code."""

    CONFIRMED = "CONFIRMED"
    DISPUTED = "DISPUTED"
    ESCALATED = "ESCALATED"
    SKIPPED = "SKIPPED"


@dataclass
class InspectionResult:
    """Validation outcome for a single ArchitecturalInsight."""

    insight_title: str
    outcome: ValidationOutcome
    evidence: str
    edge_type: str = ""


def ast_contains_call(source_file: Path, target_label: str) -> bool:
    """Returns True if target_label appears as a function call in source_file AST."""
    tree = ast.parse(source_file.read_text(encoding="utf-8", errors="replace"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = ""
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr
            if name == target_label:
                return True
    return False


def validate_semantic_duplicate(edge: GraphEdge, graph: Graph) -> ValidationOutcome:
    """Validates whether semantically similar nodes are actually duplicates."""
    source_node = graph.get_node(edge.source_id)
    target_node = graph.get_node(edge.target_id)
    if not source_node or not target_node:
        return ValidationOutcome.SKIPPED

    logger.info(
        "SemanticDuplicateValidator: Node '%s' and '%s' are semantically similar. "
        "Defensively disputing merge until call sites and tests are verified.",
        source_node.label,
        target_node.label,
    )
    return ValidationOutcome.DISPUTED


def build_hub_node_prompt(
    insight: ArchitecturalInsight, graph: Graph, repo_path: Path
) -> str | None:
    """Builds the prompt for verifying a hub node insight, reading source code if available."""
    if insight.title.startswith("Hub:") and insight.source_node_ids:
        node_id = insight.source_node_ids[0]
        node = graph.get_node(node_id)
        if node and node.file_path:
            file_path = repo_path / node.file_path
            if file_path.exists():
                code = file_path.read_text(encoding="utf-8", errors="replace")
                return (
                    "You are the CodeInspectorAgent. Evaluate the hub node "
                    f"insight '{insight.title}'.\n"
                    f"Here is the real source code for {node.file_path}:\n"
                    f"```python\n{code}\n```\n"
                    "Analyze this code to confirm its role. You MUST quote actual lines of code."
                )
    return None


def validate_edge(edge: GraphEdge, graph: Graph, repo_path: Path) -> ValidationOutcome:
    """Validates a single edge by checking source file AST for the call."""
    if edge.edge_type == EDGE_TYPE_AMBIGUOUS:
        return ValidationOutcome.ESCALATED

    if edge.label == "semantically_similar_to":
        return validate_semantic_duplicate(edge, graph)

    source_node = graph.get_node(edge.source_id)
    target_node = graph.get_node(edge.target_id)
    if not source_node or not target_node:
        return ValidationOutcome.SKIPPED

    source_file = repo_path / source_node.file_path
    if not source_file.exists() or source_file.suffix != ".py":
        return ValidationOutcome.SKIPPED

    try:
        found = ast_contains_call(source_file, target_node.label)
        return ValidationOutcome.CONFIRMED if found else ValidationOutcome.DISPUTED
    except (SyntaxError, OSError) as exc:
        logger.warning("AST parse error for %s: %s", source_file, exc)
        return ValidationOutcome.SKIPPED
