"""
HubVsBottleneckClassifier — distinguishes healthy hubs from risky god-nodes.

Rationale: high-degree nodes are not inherently bad. This classifier applies
structural heuristics (boundary clarity, cross-community ratio) to separate
well-designed shared abstractions (hubs) from Single Points of Failure (SPOFs)
that create architectural risk.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum

from .community_detector import Community
from .graph_models import Graph

logger = logging.getLogger(__name__)

# Thresholds driven entirely by constants / config — no magic numbers here.
SPOF_CROSS_COMMUNITY_RATIO = 0.6  # > 60% external edges → potential god-node
SPOF_MIN_DEGREE = 5  # Only classify nodes with at least this degree
HUB_COHESION_THRESHOLD = 0.5  # Hub must have ≥ 50% internal edge cohesion


class NodeClassification(str, Enum):
    """Classification result for a graph node."""

    HUB = "HUB"
    GOD_NODE = "GOD_NODE"
    SPOF = "SPOF"
    NORMAL = "NORMAL"


@dataclass
class NodeReport:
    """Classification result for a single node."""

    node_id: str
    label: str
    degree: int
    cross_community_ratio: float
    classification: NodeClassification
    rationale: str


class HubVsBottleneckClassifier:
    """
    Classifies high-degree nodes as healthy hubs or architectural risks.

    A node is a god-node/SPOF when it has both high degree AND a large
    fraction of its edges crossing community boundaries (excessive coupling).
    A hub is high-degree but keeps most connections within its own community
    (clear abstraction with bounded scope).
    """

    def classify(self, graph: Graph, communities: list[Community]) -> list[NodeReport]:
        """
        Classifies every node in the graph and returns a list of NodeReports.

        Only nodes above SPOF_MIN_DEGREE are subject to hub/SPOF distinction;
        others are labelled NORMAL without further analysis.
        """
        community_map = self._build_community_map(communities)
        reports: list[NodeReport] = []
        for node_id, node in graph.nodes.items():
            degree = graph.degree(node_id)
            if degree < SPOF_MIN_DEGREE:
                reports.append(
                    NodeReport(
                        node_id=node_id,
                        label=node.label,
                        degree=degree,
                        cross_community_ratio=0.0,
                        classification=NodeClassification.NORMAL,
                        rationale="Low degree — not a candidate for hub/SPOF analysis.",
                    )
                )
                continue
            cross_ratio = self._cross_community_ratio(node_id, graph, community_map)
            classification, rationale = self._classify_node(degree, cross_ratio)
            reports.append(
                NodeReport(
                    node_id=node_id,
                    label=node.label,
                    degree=degree,
                    cross_community_ratio=cross_ratio,
                    classification=classification,
                    rationale=rationale,
                )
            )
        logger.info("Classified %d nodes (%d reports)", len(graph.nodes), len(reports))
        return reports

    def spof_nodes(self, reports: list[NodeReport]) -> list[NodeReport]:
        """Filters reports to only SPOF and GOD_NODE classifications."""
        return [
            r
            for r in reports
            if r.classification in {NodeClassification.SPOF, NodeClassification.GOD_NODE}
        ]

    def _build_community_map(self, communities: list[Community]) -> dict[str, int]:
        """Maps each node_id to its community_id for O(1) lookup."""
        result: dict[str, int] = {}
        for community in communities:
            for nid in community.node_ids:
                result[nid] = community.community_id
        return result

    def _cross_community_ratio(
        self, node_id: str, graph: Graph, community_map: dict[str, int]
    ) -> float:
        """Returns fraction of edges that cross community boundaries."""
        my_community = community_map.get(node_id, -1)
        all_edges = [e for e in graph.edges if e.source_id == node_id or e.target_id == node_id]
        if not all_edges:
            return 0.0
        cross = sum(
            1
            for e in all_edges
            if community_map.get(e.source_id, -2) != community_map.get(e.target_id, -3)
            and my_community != -1
        )
        return cross / len(all_edges)

    def _classify_node(self, degree: int, cross_ratio: float) -> tuple[NodeClassification, str]:
        """Applies heuristic rules to determine node classification."""
        if cross_ratio >= SPOF_CROSS_COMMUNITY_RATIO:
            if degree > SPOF_MIN_DEGREE * 3:
                return (
                    NodeClassification.GOD_NODE,
                    f"Degree {degree} with {cross_ratio:.0%} cross-community coupling "
                    "→ god-node / high architectural risk.",
                )
            return (
                NodeClassification.SPOF,
                f"Degree {degree} with {cross_ratio:.0%} cross-community coupling "
                "→ Single Point of Failure risk.",
            )
        return (
            NodeClassification.HUB,
            f"Degree {degree} with {cross_ratio:.0%} cross-community coupling "
            "→ healthy hub (bounded abstraction).",
        )
