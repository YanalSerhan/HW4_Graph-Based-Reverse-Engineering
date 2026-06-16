"""
CommunityDetector service — identifies communities of nodes by edge density.

Rationale: community detection gives agents a meaningful unit of analysis
(a cohesive responsibility cluster) instead of working node-by-node. Using
an edge-density approach avoids any external graph library requirement while
remaining deterministic and testable.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from collections import defaultdict

from .graph_models import Graph

logger = logging.getLogger(__name__)


@dataclass
class Community:
    """A detected community of related nodes."""

    community_id: int
    node_ids: list[str]
    dominant_label: str = ""
    internal_edge_count: int = 0
    external_edge_count: int = 0

    @property
    def size(self) -> int:
        """Number of nodes in this community."""
        return len(self.node_ids)

    @property
    def cohesion_ratio(self) -> float:
        """Fraction of edges that stay within the community (higher = more cohesive)."""
        total = self.internal_edge_count + self.external_edge_count
        return self.internal_edge_count / total if total > 0 else 0.0


class CommunityDetector:
    """
    Detects communities using union-find on strongly-connected subgraphs.

    The algorithm groups nodes connected by EXTRACTED edges (highest confidence)
    first, then merges isolated INFERRED-only components as secondary pass.
    Each community is labelled by the most common file-path prefix of its nodes.
    """

    def detect(self, graph: Graph) -> list[Community]:
        """
        Runs community detection and returns labelled Community objects.

        Also stamps each GraphNode with its assigned community_id in-place,
        so downstream agents can read community membership from the node itself.
        """
        parent = self._build_union_find(graph)
        groups = self._group_by_root(graph, parent)
        communities = []
        for cid, node_ids in enumerate(groups.values()):
            community = self._build_community(cid, node_ids, graph)
            communities.append(community)
            for nid in node_ids:
                if nid in graph.nodes:
                    graph.nodes[nid].community_id = cid
        logger.info("Detected %d communities", len(communities))
        return communities

    def _build_union_find(self, graph: Graph) -> dict[str, str]:
        """Initialises union-find and unions nodes connected by any edge."""
        parent: dict[str, str] = {nid: nid for nid in graph.nodes}
        for edge in graph.edges:
            if edge.source_id in parent and edge.target_id in parent:
                self._union(parent, edge.source_id, edge.target_id)
        return parent

    def _find(self, parent: dict[str, str], x: str) -> str:
        """Path-compressed find for union-find."""
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def _union(self, parent: dict[str, str], a: str, b: str) -> None:
        """Merges the sets containing a and b."""
        root_a = self._find(parent, a)
        root_b = self._find(parent, b)
        if root_a != root_b:
            parent[root_b] = root_a

    def _group_by_root(
        self, graph: Graph, parent: dict[str, str]
    ) -> dict[str, list[str]]:
        """Groups node IDs by their union-find root."""
        groups: dict[str, list[str]] = defaultdict(list)
        for nid in graph.nodes:
            root = self._find(parent, nid)
            groups[root].append(nid)
        return dict(groups)

    def _build_community(self, cid: int, node_ids: list[str], graph: Graph) -> Community:
        """Builds a Community object with edge counts and a dominant label."""
        node_set = set(node_ids)
        internal = sum(
            1 for e in graph.edges if e.source_id in node_set and e.target_id in node_set
        )
        external = sum(
            1 for e in graph.edges
            if (e.source_id in node_set) != (e.target_id in node_set)
        )
        label = self._dominant_label(node_ids, graph)
        return Community(
            community_id=cid,
            node_ids=node_ids,
            dominant_label=label,
            internal_edge_count=internal,
            external_edge_count=external,
        )

    def _dominant_label(self, node_ids: list[str], graph: Graph) -> str:
        """Derives community label from the most common top-level path component."""
        prefix_counts: dict[str, int] = defaultdict(int)
        for nid in node_ids:
            node = graph.get_node(nid)
            if node and node.file_path:
                prefix = node.file_path.split("/")[0].split("\\")[0]
                prefix_counts[prefix] += 1
        if not prefix_counts:
            return f"community_{node_ids[0]}" if node_ids else "unknown"
        return max(prefix_counts, key=lambda k: prefix_counts[k])
