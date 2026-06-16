"""Unit tests for community_detector.py — CommunityDetector, Community."""

from __future__ import annotations

import pytest

from graph_rev_eng.constants import EDGE_TYPE_EXTRACTED
from graph_rev_eng.services.community_detector import Community, CommunityDetector
from graph_rev_eng.services.graph_models import Graph, GraphEdge, GraphNode


class TestCommunity:
    def test_size(self):
        c = Community(0, ["a", "b", "c"])
        assert c.size == 3

    def test_cohesion_ratio_all_internal(self):
        c = Community(0, ["a", "b"], internal_edge_count=5, external_edge_count=0)
        assert c.cohesion_ratio == 1.0

    def test_cohesion_ratio_all_external(self):
        c = Community(0, ["a"], internal_edge_count=0, external_edge_count=3)
        assert c.cohesion_ratio == 0.0

    def test_cohesion_ratio_mixed(self):
        c = Community(0, ["a", "b"], internal_edge_count=3, external_edge_count=1)
        assert c.cohesion_ratio == pytest.approx(0.75)

    def test_cohesion_ratio_no_edges(self):
        c = Community(0, ["a"])
        assert c.cohesion_ratio == 0.0


class TestCommunityDetector:
    def test_single_node_one_community(self):
        graph = Graph(nodes={"a": GraphNode("a", "A", "module", "src/a.py")})
        communities = CommunityDetector().detect(graph)
        assert len(communities) == 1

    def test_connected_nodes_merge(self, simple_graph: Graph):
        communities = CommunityDetector().detect(simple_graph)
        # All 4 nodes are connected via edges — should be 1 community
        assert len(communities) == 1

    def test_disconnected_nodes_separate_communities(self):
        graph = Graph(
            nodes={
                "a": GraphNode("a", "A", "module", "src/a.py"),
                "b": GraphNode("b", "B", "module", "src/b.py"),
            },
            edges=[],  # no edges — each node is its own community
        )
        communities = CommunityDetector().detect(graph)
        assert len(communities) == 2

    def test_community_id_stamped_on_nodes(self, simple_graph: Graph):
        CommunityDetector().detect(simple_graph)
        for node in simple_graph.nodes.values():
            assert node.community_id >= 0

    def test_empty_graph_returns_empty(self, empty_graph: Graph):
        communities = CommunityDetector().detect(empty_graph)
        assert communities == []

    def test_dominant_label_derived_from_file_path(self):
        graph = Graph(
            nodes={
                "a": GraphNode("a", "A", "module", "services/svc_a.py"),
                "b": GraphNode("b", "B", "module", "services/svc_b.py"),
            },
            edges=[GraphEdge("a", "b", EDGE_TYPE_EXTRACTED)],
        )
        communities = CommunityDetector().detect(graph)
        assert len(communities) == 1
        assert communities[0].dominant_label == "services"
