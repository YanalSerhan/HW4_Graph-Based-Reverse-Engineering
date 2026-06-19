"""
graph_differ_format.py — Markdown formatting for GraphDiff.
"""
from typing import TYPE_CHECKING

from .graph_models import Graph

if TYPE_CHECKING:
    from .graph_differ import GraphDiff


def format_graph_diff(diff: "GraphDiff", graph_before: Graph, graph_after: Graph) -> str:
    """Generates the Markdown representation of a graph diff."""
    md = [
        "# Architectural Graph Diff — Before vs After Bug Fix",
        "",
        "## Nodes Added",
        "| Node | Type | Reason |",
        "|---|---|---|",
    ]
    for n in diff.nodes_added:
        md.append(f"| {n.label} | {n.node_type} | Extracted from fixed code |")

    md.extend(["", "## Nodes Removed", "| Node | Type | Reason |", "|---|---|---|"])
    for n in diff.nodes_removed:
        md.append(f"| {n.label} | {n.node_type} | Removed/Fixed |")

    md.extend(
        [
            "",
            "## Edges Changed",
            "| Source | Target | Before | After | Interpretation |",
            "|---|---|---|---|---|",
        ]
    )
    for e in diff.edges_removed:
        src = graph_before.nodes.get(e.source_id)
        tgt = graph_before.nodes.get(e.target_id)
        src_lbl = src.label if src else e.source_id
        tgt_lbl = tgt.label if tgt else e.target_id
        md.append(f"| {src_lbl} | {tgt_lbl} | {e.edge_type} | (removed) | Edge resolved |")

    for e in diff.edges_added:
        src = graph_after.nodes.get(e.source_id)
        tgt = graph_after.nodes.get(e.target_id)
        src_lbl = src.label if src else e.source_id
        tgt_lbl = tgt.label if tgt else e.target_id
        md.append(f"| {src_lbl} | {tgt_lbl} | (none) | {e.edge_type} | New relationship |")

    delta_nodes = len(graph_after.nodes) - len(graph_before.nodes)
    delta_edges = len(graph_after.edges) - len(graph_before.edges)
    delta_error = len(diff.error_nodes_after) - len(diff.error_nodes_before)
    delta_amb = len(diff.ambiguous_edges_after) - len(diff.ambiguous_edges_before)

    def fmt(d):
        return f"{d:+d}" if d != 0 else "0"

    md.extend(
        [
            "",
            "## Architectural Health Score",
            "| Metric | Before | After | Delta |",
            "|--------|--------|-------|-------|",
            (
                f"| Total nodes | {len(graph_before.nodes)} | {len(graph_after.nodes)} "
                f"| {fmt(delta_nodes)} |"
            ),
            (
                f"| Total edges | {len(graph_before.edges)} | {len(graph_after.edges)} "
                f"| {fmt(delta_edges)} |"
            ),
            (
                f"| Error nodes | {len(diff.error_nodes_before)} | {len(diff.error_nodes_after)} "
                f"| {fmt(delta_error)} ✅ |"
            ),
            (
                f"| Ambiguous edges | {len(diff.ambiguous_edges_before)} | "
                f"{len(diff.ambiguous_edges_after)} | {fmt(delta_amb)} ✅ |"
            ),
        ]
    )

    return "\n".join(md)
