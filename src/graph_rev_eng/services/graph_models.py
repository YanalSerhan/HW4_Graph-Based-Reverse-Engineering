"""
Graph domain models — canonical dataclasses for all graph operations.

These are the single source of truth for node/edge/graph representation,
used by every service and agent in the pipeline. Keeping them here avoids
duplication and circular imports.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GraphNode:
    """Represents a single node (file, class, function, module) in the graph."""

    node_id: str
    label: str
    node_type: str  # "module" | "class" | "function" | "variable"
    file_path: str = ""
    line_number: int = 0
    community_id: int = -1
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphEdge:
    """Represents a typed, directional relationship between two nodes."""

    source_id: str
    target_id: str
    edge_type: str  # EXTRACTED | INFERRED | AMBIGUOUS
    confidence: float = 1.0
    label: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Hyperedge:
    """
    A group connection linking multiple member nodes simultaneously.

    Hyperedges represent collective relationships (e.g., a shared interface
    implemented by several classes) that cannot be reduced to pairwise edges
    without losing group semantics.
    """

    hyperedge_id: str
    member_ids: list[str]
    edge_type: str
    confidence: float = 1.0
    label: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate_members(self, node_ids: set[str]) -> list[str]:
        """Returns member IDs that are missing from the graph node set."""
        return [mid for mid in self.member_ids if mid not in node_ids]


@dataclass
class Graph:
    """
    In-memory graph representation produced by parsing graph.json.

    Centralises all graph data so every agent works with one consistent object
    instead of re-parsing the JSON file independently.
    """

    nodes: dict[str, GraphNode] = field(default_factory=dict)
    edges: list[GraphEdge] = field(default_factory=list)
    hyperedges: list[Hyperedge] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_node(self, node_id: str) -> GraphNode | None:
        """Returns the node for the given ID, or None if absent."""
        return self.nodes.get(node_id)

    def neighbors(self, node_id: str) -> list[str]:
        """Returns IDs of all nodes directly connected to node_id (outgoing)."""
        return [e.target_id for e in self.edges if e.source_id == node_id]

    def in_degree(self, node_id: str) -> int:
        """Returns the number of edges pointing into node_id."""
        return sum(1 for e in self.edges if e.target_id == node_id)

    def out_degree(self, node_id: str) -> int:
        """Returns the number of edges originating from node_id."""
        return sum(1 for e in self.edges if e.source_id == node_id)

    def degree(self, node_id: str) -> int:
        """Returns total degree (in + out) for node_id."""
        return self.in_degree(node_id) + self.out_degree(node_id)

    def edges_of_type(self, edge_type: str) -> list[GraphEdge]:
        """Returns all edges matching the given edge_type."""
        return [e for e in self.edges if e.edge_type == edge_type]

    def node_ids(self) -> set[str]:
        """Returns the set of all node IDs."""
        return set(self.nodes.keys())
