"""Unit tests for graph_loader.py — GraphLoader."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from graph_rev_eng.constants import (
    EDGE_TYPE_AMBIGUOUS,
    EDGE_TYPE_EXTRACTED,
    EDGE_TYPE_INFERRED,
)
from graph_rev_eng.services.graph_loader import GraphLoader, GraphValidationError


class TestGraphLoader:
    def test_load_valid_graph(self, graph_json_file: Path):
        graph = GraphLoader().load(graph_json_file)
        assert len(graph.nodes) == 4
        assert len(graph.edges) == 3

    def test_load_all_edge_types_parsed(self, graph_json_file: Path):
        graph = GraphLoader().load(graph_json_file)
        types = {e.edge_type for e in graph.edges}
        assert EDGE_TYPE_EXTRACTED in types
        assert EDGE_TYPE_INFERRED in types
        assert EDGE_TYPE_AMBIGUOUS in types

    def test_load_missing_file_raises(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            GraphLoader().load(tmp_path / "nonexistent.json")

    def test_load_metadata_preserved(self, graph_json_file: Path):
        graph = GraphLoader().load(graph_json_file)
        assert graph.metadata.get("version") == "1.0"

    def test_hyperedge_with_unknown_member_raises(self, tmp_path: Path):
        data = {
            "nodes": [{"id": "a", "label": "A", "type": "module"}],
            "edges": [],
            "hyperedges": [{"id": "he1", "members": ["a", "UNKNOWN"], "type": "EXTRACTED"}],
        }
        path = tmp_path / "graph.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(GraphValidationError):
            GraphLoader().load(path)

    def test_load_hyperedge_with_known_members(self, tmp_path: Path):
        data = {
            "nodes": [
                {"id": "a", "label": "A", "type": "module"},
                {"id": "b", "label": "B", "type": "module"},
            ],
            "edges": [],
            "hyperedges": [{"id": "he1", "members": ["a", "b"], "type": "EXTRACTED"}],
        }
        path = tmp_path / "graph.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        graph = GraphLoader().load(path)
        assert len(graph.hyperedges) == 1

    def test_empty_graph_loads(self, tmp_path: Path):
        data = {"nodes": [], "edges": [], "hyperedges": []}
        path = tmp_path / "graph.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        graph = GraphLoader().load(path)
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0

    def test_edge_type_uppercased(self, tmp_path: Path):
        data = {
            "nodes": [
                {"id": "a", "label": "A", "type": "module"},
                {"id": "b", "label": "B", "type": "module"},
            ],
            "edges": [{"source": "a", "target": "b", "type": "extracted"}],
            "hyperedges": [],
        }
        path = tmp_path / "graph.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        graph = GraphLoader().load(path)
        assert graph.edges[0].edge_type == EDGE_TYPE_EXTRACTED
