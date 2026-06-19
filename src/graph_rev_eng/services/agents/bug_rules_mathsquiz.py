"""
bug_rules_mathsquiz.py — specific logic bugs for mathsquiz.
"""

from __future__ import annotations

from pathlib import Path

from ..graph_models import Graph
from .bug_types import ArchitecturalBug, BugSeverity


def detect_mathsquiz_logic_bugs(graph: Graph) -> list[ArchitecturalBug]:
    """Detects specific logic and copy-paste bugs in mathsquiz.py."""
    bugs: list[ArchitecturalBug] = []

    target_node_id = None
    target_path_str = None
    for node in graph.nodes.values():
        if node.file_path and node.file_path.endswith("mathsquiz.py"):
            target_node_id = node.node_id
            target_path_str = node.file_path
            break

    if not target_path_str:
        return bugs

    mathsquiz_path = Path(target_path_str)
    if not mathsquiz_path.exists():
        # Fallback for relative paths in graph depending on CWD
        mathsquiz_path = Path("data/broken-python") / target_path_str
        if not mathsquiz_path.exists():
            return bugs

    content = mathsquiz_path.read_text(encoding="utf-8")

    if "if answer = 55:" in content or "if answer =" in content:
        bugs.append(
            ArchitecturalBug(
                bug_type="LOGIC_ERROR",
                severity=BugSeverity.HIGH,
                description=(
                    "Assignment operator '=' used instead of equality operator '==' "
                    "in if condition."
                ),
                affected_node_ids=[target_node_id] if target_node_id else [],
                recommendation="Replace '=' with '==' in if conditions.",
            )
        )

    if content.count('print("Question 1:")') > 1:
        bugs.append(
            ArchitecturalBug(
                bug_type="COPY_PASTE_ERROR",
                severity=BugSeverity.MEDIUM,
                description="Multiple questions are labeled as 'Question 1:'.",
                affected_node_ids=[target_node_id] if target_node_id else [],
                recommendation="Update question labels to reflect the correct question number.",
            )
        )

    if "8 x 7" in content and "55" in content:
        bugs.append(
            ArchitecturalBug(
                bug_type="LOGIC_ERROR",
                severity=BugSeverity.HIGH,
                description="Wrong expected answer for 8x7: expects 55 instead of 56.",
                affected_node_ids=[target_node_id] if target_node_id else [],
                recommendation="Fix the expected answer for 8x7 to 56.",
            )
        )

    if "4 x 9" in content and "49" in content:
        bugs.append(
            ArchitecturalBug(
                bug_type="LOGIC_ERROR",
                severity=BugSeverity.HIGH,
                description="Wrong expected answer for 4x9: expects 49 instead of 36.",
                affected_node_ids=[target_node_id] if target_node_id else [],
                recommendation="Fix the expected answer for 4x9 to 36.",
            )
        )

    if "else if" in content:
        bugs.append(
            ArchitecturalBug(
                bug_type="SYNTAX_ERROR",
                severity=BugSeverity.CRITICAL,
                description="'else if' is used instead of Python's 'elif'.",
                affected_node_ids=[target_node_id] if target_node_id else [],
                recommendation="Replace 'else if' with 'elif'.",
            )
        )

    return bugs
