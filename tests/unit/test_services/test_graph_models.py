"""Unit tests for graph_models.py — GraphNode, GraphEdge, Hyperedge, Graph."""

from __future__ import annotations

import pytest

from graph_rev_eng.services.graph_models import Graph, GraphEdge, GraphNode, Hyperedge
from graph_rev_eng.constants import (
    EDGE_TYPE_EXTRACTED,
    EDGE_TYPE_INFERRED,
    EDGE_TYPE_AMBIGUOUS,
)


class TestGraphNode:
    def test_default_community_id(self):
        node = GraphNode("n1", "module_a", "module")
        assert node.community_id == -1

    def test_metadata_defaults_empty(self):
        node = GraphNode("n1", "label", "class")
        assert node.metadata == {}


class TestHyperedge:
    def test_validate_members_all_present(self):
        he = Hyperedge("he1", ["a", "b", "c"], EDGE_TYPE_EXTRACTED)
        assert he.validate_members({"a", "b", "c", "d"}) == []

    def test_validate_members_missing(self):
        he = Hyperedge("he1", ["a", "b", "x"], EDGE_TYPE_INFERRED)
        missing = he.validate_members({"a", "b"})
        assert missing == ["x"]

    def test_validate_members_all_missing(self):
        he = Hyperedge("he1", ["x", "y"], EDGE_TYPE_AMBIGUOUS)
        assert he.validate_members(set()) == ["x", "y"]


class TestGraph:
    def test_get_node_returns_correct_node(self, simple_graph: Graph):
        node = simple_graph.get_node("n1")
        assert node is not None
        assert node.label == "module_a"

    def test_get_node_missing_returns_none(self, simple_graph: Graph):
        assert simple_graph.get_node("nonexistent") is None

    def test_neighbors(self, simple_graph: Graph):
        neighbors = simple_graph.neighbors("n1")
        assert "n2" in neighbors

    def test_in_degree(self, simple_graph: Graph):
        assert simple_graph.in_degree("n2") == 1

    def test_out_degree(self, simple_graph: Graph):
        assert simple_graph.out_degree("n1") == 1

    def test_degree_sum(self, simple_graph: Graph):
        assert simple_graph.degree("n2") == 2  # 1 in + 1 out

    def test_edges_of_type_extracted(self, simple_graph: Graph):
        extracted = simple_graph.edges_of_type(EDGE_TYPE_EXTRACTED)
        assert len(extracted) == 1
        assert extracted[0].source_id == "n1"

    def test_edges_of_type_ambiguous(self, simple_graph: Graph):
        ambiguous = simple_graph.edges_of_type(EDGE_TYPE_AMBIGUOUS)
        assert len(ambiguous) == 1

    def test_node_ids_returns_set(self, simple_graph: Graph):
        ids = simple_graph.node_ids()
        assert isinstance(ids, set)
        assert "n1" in ids

    def test_empty_graph_degree(self, empty_graph: Graph):
        assert empty_graph.degree("any") == 0

    def test_empty_graph_neighbors(self, empty_graph: Graph):
        assert empty_graph.neighbors("any") == []
