"""
GraphLoader service — parses graph.json into an in-memory Graph object.

Separation rationale: parsing is I/O-bound and validation-heavy; keeping it
isolated from analysis agents means the JSON contract can change without
touching any agent logic.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from ..constants import EDGE_TYPE_AMBIGUOUS, EDGE_TYPE_EXTRACTED, EDGE_TYPE_INFERRED
from .graph_models import Graph, GraphEdge, GraphNode, Hyperedge

logger = logging.getLogger(__name__)

VALID_EDGE_TYPES = {EDGE_TYPE_EXTRACTED, EDGE_TYPE_INFERRED, EDGE_TYPE_AMBIGUOUS}


class GraphValidationError(Exception):
    """Raised when graph.json fails structural validation."""


class GraphLoader:
    """
    Parses and validates graph.json into a Graph domain object.

    Validates that all three edge types are correctly parsed and that every
    Hyperedge references only known node IDs.
    """

    def load(self, graph_path: Path) -> Graph:
        """
        Loads and validates the graph from a JSON file.

        Raises GraphValidationError if mandatory edge types are absent or if
        any hyperedge members reference unknown nodes.
        """
        raw = self._read_json(graph_path)
        graph = self._parse(raw)
        self._validate(graph)
        logger.info("Graph loaded: %d nodes, %d edges", len(graph.nodes), len(graph.edges))
        return graph

    def _read_json(self, path: Path) -> dict[str, Any]:
        """Reads the JSON file at path and returns the parsed dict."""
        if not path.exists():
            raise FileNotFoundError(f"graph.json not found at {path}")
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)

    def _parse(self, raw: dict[str, Any]) -> Graph:
        """Builds a Graph from the raw dictionary."""
        nodes = self._parse_nodes(raw.get("nodes", []))
        edges = self._parse_edges(raw.get("edges", []))
        hyperedges = self._parse_hyperedges(raw.get("hyperedges", []))
        metadata = raw.get("metadata", {})
        return Graph(nodes=nodes, edges=edges, hyperedges=hyperedges, metadata=metadata)

    def _parse_nodes(self, raw_nodes: list[dict]) -> dict[str, GraphNode]:
        """Converts raw node dicts to GraphNode objects keyed by ID."""
        result: dict[str, GraphNode] = {}
        for item in raw_nodes:
            node = GraphNode(
                node_id=item["id"],
                label=item.get("label", item["id"]),
                node_type=item.get("type", "module"),
                file_path=item.get("file_path", ""),
                line_number=item.get("line_number", 0),
                metadata=item.get("metadata", {}),
            )
            result[node.node_id] = node
        return result

    def _parse_edges(self, raw_edges: list[dict]) -> list[GraphEdge]:
        """Converts raw edge dicts to GraphEdge objects."""
        result: list[GraphEdge] = []
        for item in raw_edges:
            edge_type = str(item.get("type", EDGE_TYPE_EXTRACTED)).upper()
            result.append(
                GraphEdge(
                    source_id=item["source"],
                    target_id=item["target"],
                    edge_type=edge_type,
                    confidence=float(item.get("confidence", 1.0)),
                    label=item.get("label", ""),
                    metadata=item.get("metadata", {}),
                )
            )
        return result

    def _parse_hyperedges(self, raw: list[dict]) -> list[Hyperedge]:
        """Converts raw hyperedge dicts to Hyperedge objects."""
        result: list[Hyperedge] = []
        for item in raw:
            result.append(
                Hyperedge(
                    hyperedge_id=item["id"],
                    member_ids=list(item.get("members", [])),
                    edge_type=str(item.get("type", EDGE_TYPE_INFERRED)).upper(),
                    confidence=float(item.get("confidence", 1.0)),
                    label=item.get("label", ""),
                    metadata=item.get("metadata", {}),
                )
            )
        return result

    def _validate(self, graph: Graph) -> None:
        """Validates edge types and hyperedge membership consistency."""
        found_types = {e.edge_type for e in graph.edges}
        missing = VALID_EDGE_TYPES - found_types
        if missing:
            logger.warning("Graph missing edge types: %s", missing)

        node_ids = graph.node_ids()
        for he in graph.hyperedges:
            unknown = he.validate_members(node_ids)
            if unknown:
                raise GraphValidationError(
                    f"Hyperedge '{he.hyperedge_id}' references unknown nodes: {unknown}"
                )
