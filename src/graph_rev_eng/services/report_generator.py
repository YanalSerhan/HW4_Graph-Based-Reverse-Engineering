"""
report_generator.py — generates the GRAPH_REPORT.md narrative from a graph.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .graph_models import Graph


def generate_graph_report(graph: Graph) -> str:
    """
    Generates a markdown narrative report summarizing the graph's structural details.
    """
    total_nodes = len(graph.nodes)
    total_edges = len(graph.edges)

    extracted = len(graph.edges_of_type("EXTRACTED"))
    inferred = len(graph.edges_of_type("INFERRED"))
    ambiguous = len(graph.edges_of_type("AMBIGUOUS"))

    report = [
        "# Grphify Narrative Report",
        "",
        "## Architectural Summary",
        f"The parsed codebase contains **{total_nodes} nodes** and **{total_edges} edges**.",
        "",
        "### Edge Breakdown",
        f"- **Extracted (Deterministic):** {extracted}",
        f"- **Inferred (Heuristic):** {inferred}",
        f"- **Ambiguous (Flagged for Review):** {ambiguous}",
        "",
        "## Node Analysis",
        "Key components identified in the graph include:",
    ]

    for node in list(graph.nodes.values())[:10]:
        report.append(f"- `{node.label}` ({node.node_type})")

    if total_nodes > 10:
        report.append(f"- ... and {total_nodes - 10} more.")

    report.extend([
        "",
        "## Conclusion",
        "The graph is ready for agent inspection. "
        "Ambiguous edges must be reviewed to establish a verified structural baseline.",
    ])

    return "\n".join(report)
