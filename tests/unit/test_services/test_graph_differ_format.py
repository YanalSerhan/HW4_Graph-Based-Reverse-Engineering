"""
Tests for graph_differ_format.py
"""

from graph_rev_eng.services.graph_differ import GraphDiff
from graph_rev_eng.services.graph_differ_format import format_graph_diff
from graph_rev_eng.services.graph_models import Graph, GraphEdge, GraphNode


def test_format_graph_diff_edges():
    g_before = Graph()
    g_before.nodes["n1"] = GraphNode(
        node_id="n1", label="Node 1", node_type="module", file_path="f1"
    )
    g_before.nodes["n2"] = GraphNode(
        node_id="n2", label="Node 2", node_type="module", file_path="f2"
    )
    g_before.edges.append(GraphEdge("n1", "n2", "calls", label="calls"))

    g_after = Graph()
    g_after.nodes["n2"] = GraphNode(
        node_id="n2", label="Node 2", node_type="module", file_path="f2"
    )
    g_after.nodes["n3"] = GraphNode(
        node_id="n3", label="Node 3", node_type="module", file_path="f3"
    )
    g_after.edges.append(GraphEdge("n2", "n3", "imports", label="imports"))

    diff = GraphDiff(g_before, g_after)
    md = format_graph_diff(diff, g_before, g_after)

    # Check edges removed logic (lines 35-41)
    # n1 is in graph_before, n2 is in graph_before
    assert "| Node 1 | Node 2 | calls | (removed) | Edge resolved |" in md

    # Check edges added logic (lines 42-47)
    # n2 is in graph_after, n3 is in graph_after
    assert "| Node 2 | Node 3 | (none) | imports | New relationship |" in md

    # Check fallback when node not found in graph (lines 38/39 and 45/46)
    g_before_missing = Graph()
    g_before_missing.edges.append(GraphEdge("n1", "n2", "calls", label="calls"))

    g_after_missing = Graph()
    g_after_missing.edges.append(GraphEdge("n2", "n3", "imports", label="imports"))

    diff_missing = GraphDiff(g_before_missing, g_after_missing)
    md_missing = format_graph_diff(diff_missing, g_before_missing, g_after_missing)

    assert "| n1 | n2 | calls | (removed) | Edge resolved |" in md_missing
    assert "| n2 | n3 | (none) | imports | New relationship |" in md_missing
