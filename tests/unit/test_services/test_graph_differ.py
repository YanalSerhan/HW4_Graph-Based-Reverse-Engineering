"""
Tests for GraphDiff and format_graph_diff.
"""

import json
from unittest.mock import patch

from graph_rev_eng.services.graph_differ import GraphDiff, build_graph_for_state, main, save_graph
from graph_rev_eng.services.graph_differ_format import format_graph_diff
from graph_rev_eng.services.graph_models import Graph, GraphEdge, GraphNode


def test_diff_identical_graphs():
    """Test diffing two identical graphs produces zero added/removed nodes."""
    g1 = Graph()
    g1.nodes["n1"] = GraphNode(node_id="n1", label="Node 1", node_type="module", file_path="f1")
    g2 = Graph()
    g2.nodes["n1"] = GraphNode(node_id="n1", label="Node 1", node_type="module", file_path="f1")

    diff = GraphDiff(g1, g2)
    assert len(diff.nodes_added) == 0
    assert len(diff.nodes_removed) == 0
    assert len(diff.edges_added) == 0
    assert len(diff.edges_removed) == 0


def test_extra_node_removed():
    """Test a graph with an extra node produces one node in nodes_removed
    when going from more->fewer."""
    g_before = Graph()
    g_before.nodes["n1"] = GraphNode(
        node_id="n1", label="Node 1", node_type="module", file_path="f1"
    )
    g_before.nodes["n2"] = GraphNode(
        node_id="n2", label="Node 2", node_type="module", file_path="f2"
    )

    g_after = Graph()
    g_after.nodes["n1"] = GraphNode(
        node_id="n1", label="Node 1", node_type="module", file_path="f1"
    )

    diff = GraphDiff(g_before, g_after)
    assert len(diff.nodes_added) == 0
    assert len(diff.nodes_removed) == 1
    assert diff.nodes_removed[0].node_id == "n2"


def test_error_node_removed():
    """Test removing an error node is detected correctly."""
    g_before = Graph()
    g_before.nodes["e1"] = GraphNode(
        node_id="e1", label="SyntaxError", node_type="error", file_path="f1"
    )
    g_before.nodes["n1"] = GraphNode(
        node_id="n1", label="Node 1", node_type="module", file_path="f1"
    )

    g_after = Graph()
    g_after.nodes["n1"] = GraphNode(
        node_id="n1", label="Node 1", node_type="module", file_path="f1"
    )

    diff = GraphDiff(g_before, g_after)
    assert len(diff.error_nodes_before) == 1
    assert len(diff.error_nodes_after) == 0
    assert diff.error_nodes_before[0].node_id == "e1"


def test_architectural_health_score_computation():
    """Test the architectural health score computation in format_graph_diff."""
    g_before = Graph()
    g_before.nodes["e1"] = GraphNode(
        node_id="e1", label="SyntaxError", node_type="error", file_path="f1"
    )
    g_before.nodes["n1"] = GraphNode(
        node_id="n1", label="Node 1", node_type="module", file_path="f1"
    )

    g_after = Graph()
    g_after.nodes["n1"] = GraphNode(
        node_id="n1", label="Node 1", node_type="module", file_path="f1"
    )
    g_after.nodes["n2"] = GraphNode(
        node_id="n2", label="Node 2", node_type="module", file_path="f2"
    )

    diff = GraphDiff(g_before, g_after)
    md = format_graph_diff(diff, g_before, g_after)

    # Check that error nodes drop is noted correctly (-1)
    assert "| Error nodes | 1 | 0 | -1 ✅ |" in md

    # Check that total nodes changed from 2 to 2 (delta 0)
    assert "| Total nodes | 2 | 2 | 0 |" in md


def test_diff_edges_added_and_removed():
    """Test edges_added and edges_removed paths."""
    g_before = Graph()
    g_before.edges.append(GraphEdge("n1", "n2", "calls", label="calls"))

    g_after = Graph()
    g_after.edges.append(GraphEdge("n2", "n3", "calls", label="calls"))

    diff = GraphDiff(g_before, g_after)
    assert len(diff.edges_removed) == 1
    assert diff.edges_removed[0].source_id == "n1"

    assert len(diff.edges_added) == 1
    assert diff.edges_added[0].source_id == "n2"

    assert len(diff.confidence_changes) == 0


def test_build_graph_for_state(tmp_path):
    # Create dummy python file
    p = tmp_path / "dummy.py"
    p.write_text("def foo(): pass", encoding="utf-8")
    graph = build_graph_for_state(tmp_path)
    assert len(graph.nodes) > 0


def test_save_graph(tmp_path):
    g = Graph()
    g.nodes["n1"] = GraphNode(node_id="n1", label="L", node_type="module", file_path="P")
    p = tmp_path / "graph.json"
    save_graph(g, p)
    data = json.loads(p.read_text())
    assert len(data["nodes"]) == 1
    assert data["nodes"][0]["id"] == "n1"


def test_graph_differ_main():
    with (
        patch("graph_rev_eng.services.graph_differ.build_graph_for_state") as mock_build,
        patch("graph_rev_eng.services.graph_differ.save_graph"),
        patch("graph_rev_eng.services.graph_differ.shutil.move"),
        patch("graph_rev_eng.services.graph_differ.shutil.copy"),
        patch("subprocess.run"),
        patch("graph_rev_eng.services.graph_differ.Path.write_text"),
        patch("graph_rev_eng.services.graph_differ.Path.exists", return_value=True),
    ):
        mock_build.return_value = Graph()
        main()
        assert mock_build.call_count == 2
