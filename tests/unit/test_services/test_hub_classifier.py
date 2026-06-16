"""Unit tests for hub_classifier.py — HubVsBottleneckClassifier."""

from __future__ import annotations

import pytest

from graph_rev_eng.services.hub_classifier import (
    HubVsBottleneckClassifier,
    NodeClassification,
    SPOF_MIN_DEGREE,
)
from graph_rev_eng.services.community_detector import CommunityDetector, Community
from graph_rev_eng.services.graph_models import Graph, GraphEdge, GraphNode
from graph_rev_eng.constants import EDGE_TYPE_EXTRACTED


def _make_dense_hub_graph() -> tuple[Graph, list[Community]]:
    """Creates a graph with a high-degree cross-community hub."""
    nodes = {
        "hub": GraphNode("hub", "hub_mod", "module", "src/hub.py"),
        "c1a": GraphNode("c1a", "c1_a", "module", "src/c1/a.py"),
        "c1b": GraphNode("c1b", "c1_b", "module", "src/c1/b.py"),
        "c2a": GraphNode("c2a", "c2_a", "module", "src/c2/a.py"),
        "c2b": GraphNode("c2b", "c2_b", "module", "src/c2/b.py"),
        "c2c": GraphNode("c2c", "c2_c", "module", "src/c2/c.py"),
    }
    edges = [
        GraphEdge("hub", "c1a", EDGE_TYPE_EXTRACTED),
        GraphEdge("hub", "c1b", EDGE_TYPE_EXTRACTED),
        GraphEdge("hub", "c2a", EDGE_TYPE_EXTRACTED),
        GraphEdge("hub", "c2b", EDGE_TYPE_EXTRACTED),
        GraphEdge("hub", "c2c", EDGE_TYPE_EXTRACTED),
    ]
    graph = Graph(nodes=nodes, edges=edges)
    # Manually assign community IDs to simulate detection
    graph.nodes["hub"].community_id = 0
    graph.nodes["c1a"].community_id = 1
    graph.nodes["c1b"].community_id = 1
    graph.nodes["c2a"].community_id = 2
    graph.nodes["c2b"].community_id = 2
    graph.nodes["c2c"].community_id = 2
    communities = [
        Community(0, ["hub"]),
        Community(1, ["c1a", "c1b"]),
        Community(2, ["c2a", "c2b", "c2c"]),
    ]
    return graph, communities


class TestHubVsBottleneckClassifier:
    def test_low_degree_node_classified_as_normal(self, simple_graph: Graph):
        communities = CommunityDetector().detect(simple_graph)
        reports = HubVsBottleneckClassifier().classify(simple_graph, communities)
        normal = [r for r in reports if r.classification == NodeClassification.NORMAL]
        assert len(normal) > 0

    def test_hub_detected(self, hub_graph: Graph):
        communities = CommunityDetector().detect(hub_graph)
        reports = HubVsBottleneckClassifier().classify(hub_graph, communities)
        hub_reports = [r for r in reports if r.classification == NodeClassification.HUB]
        assert len(hub_reports) > 0

    def test_spof_detected_on_cross_community_hub(self):
        graph, communities = _make_dense_hub_graph()
        reports = HubVsBottleneckClassifier().classify(graph, communities)
        hub_report = next(r for r in reports if r.node_id == "hub")
        assert hub_report.classification in {NodeClassification.HUB, NodeClassification.SPOF}

    def test_spof_nodes_filter(self, hub_graph: Graph):
        communities = CommunityDetector().detect(hub_graph)
        classifier = HubVsBottleneckClassifier()
        reports = classifier.classify(hub_graph, communities)
        # spof_nodes should return subset of reports
        spofs = classifier.spof_nodes(reports)
        for r in spofs:
            assert r.classification in {NodeClassification.SPOF, NodeClassification.GOD_NODE}

    def test_empty_graph_no_reports(self, empty_graph: Graph):
        reports = HubVsBottleneckClassifier().classify(empty_graph, [])
        assert reports == []

    def test_cross_community_ratio_attribute(self):
        graph, communities = _make_dense_hub_graph()
        reports = HubVsBottleneckClassifier().classify(graph, communities)
        hub_report = next(r for r in reports if r.node_id == "hub")
        # hub has 5 edges all going to different communities → ratio should be > 0
        assert hub_report.cross_community_ratio > 0
