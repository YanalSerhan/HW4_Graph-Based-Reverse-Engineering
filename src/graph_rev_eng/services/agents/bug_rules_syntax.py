"""
bug_rules_syntax.py — standalone detection rules for syntax errors.
"""

from __future__ import annotations

from ..graph_models import Graph
from .bug_types import ArchitecturalBug, BugSeverity


def detect_syntax_errors(graph: Graph) -> list[ArchitecturalBug]:
    """Detects Python 2 migration issues and syntax errors from error nodes."""
    bugs: list[ArchitecturalBug] = []
    for node in graph.nodes.values():
        if node.node_type == "error":
            label_lower = node.label.lower()
            bug_type = (
                "PYTHON_2_MIGRATION_ISSUE"
                if "print" in label_lower and "parentheses" in label_lower
                else "SYNTAX_ERROR"
            )
            bugs.append(
                ArchitecturalBug(
                    bug_type=bug_type,
                    severity=BugSeverity.CRITICAL,
                    description=f"Syntax issue found: {node.label}",
                    affected_node_ids=[node.node_id],
                    recommendation="Fix the syntax error to ensure modern Python compatibility.",
                )
            )
    return bugs
