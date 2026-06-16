"""
Shared test fixtures for the entire test suite.

All external dependencies (LLM, filesystem, GitHub clone) are mocked here
so unit tests never make real network calls.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from graph_rev_eng.constants import (
    EDGE_TYPE_AMBIGUOUS,
    EDGE_TYPE_EXTRACTED,
    EDGE_TYPE_INFERRED,
)
from graph_rev_eng.services.graph_models import Graph, GraphEdge, GraphNode
from graph_rev_eng.services.token_counter import TokenCounter

# ---------------------------------------------------------------------------
# Mock graph fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def simple_graph() -> Graph:
    """A minimal graph with one node of each edge type."""
    nodes = {
        "n1": GraphNode("n1", "module_a", "module", "src/module_a.py"),
        "n2": GraphNode("n2", "module_b", "module", "src/module_b.py"),
        "n3": GraphNode("n3", "module_c", "class", "src/module_a.py"),
        "n4": GraphNode("n4", "module_d", "function", "src/module_d.py"),
    }
    edges = [
        GraphEdge("n1", "n2", EDGE_TYPE_EXTRACTED, confidence=1.0),
        GraphEdge("n2", "n3", EDGE_TYPE_INFERRED, confidence=0.8),
        GraphEdge("n3", "n4", EDGE_TYPE_AMBIGUOUS, confidence=0.5),
    ]
    return Graph(nodes=nodes, edges=edges)


@pytest.fixture()
def hub_graph() -> Graph:
    """A graph with a high-degree hub node (n_hub connects to 8 others)."""
    nodes = {f"n{i}": GraphNode(f"n{i}", f"mod_{i}", "module", f"src/mod_{i}.py") for i in range(9)}
    nodes["n_hub"] = GraphNode("n_hub", "hub_module", "module", "src/hub.py")
    edges = [GraphEdge("n_hub", f"n{i}", EDGE_TYPE_EXTRACTED) for i in range(8)]
    # Add some cross-community-like edges
    edges += [GraphEdge(f"n{i}", f"n{i + 1}", EDGE_TYPE_EXTRACTED) for i in range(4)]
    return Graph(nodes=nodes, edges=edges)


@pytest.fixture()
def empty_graph() -> Graph:
    """An empty graph with no nodes or edges."""
    return Graph()


@pytest.fixture()
def ambiguous_only_graph() -> Graph:
    """A graph containing only AMBIGUOUS edges."""
    nodes = {
        "a": GraphNode("a", "alpha", "module", "src/alpha.py"),
        "b": GraphNode("b", "beta", "module", "src/beta.py"),
    }
    edges = [GraphEdge("a", "b", EDGE_TYPE_AMBIGUOUS, confidence=0.3)]
    return Graph(nodes=nodes, edges=edges)


@pytest.fixture()
def graph_json_file(tmp_path: Path, simple_graph: Graph) -> Path:
    """Writes a valid graph.json to a temp path and returns it."""
    data = {
        "nodes": [
            {"id": nid, "label": n.label, "type": n.node_type, "file_path": n.file_path}
            for nid, n in simple_graph.nodes.items()
        ],
        "edges": [
            {
                "source": e.source_id,
                "target": e.target_id,
                "type": e.edge_type,
                "confidence": e.confidence,
            }
            for e in simple_graph.edges
        ],
        "hyperedges": [],
        "metadata": {"version": "1.0"},
    }
    path = tmp_path / "graph.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# LLM / API mock fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_llm_call():
    """Deterministic LLM stub that returns a predictable string."""

    def _stub(prompt: str) -> str:
        return f"[MOCK RESPONSE] {len(prompt)} chars"

    return _stub


@pytest.fixture()
def token_counter() -> TokenCounter:
    """Fresh TokenCounter for each test."""
    return TokenCounter()


# ---------------------------------------------------------------------------
# Filesystem fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_repo_path(tmp_path: Path) -> Path:
    """Creates a minimal fake Python repository in a temp directory."""
    repo = tmp_path / "fake_repo"
    repo.mkdir()
    (repo / "main.py").write_text("def run():\n    pass\n", encoding="utf-8")
    (repo / "utils.py").write_text("def helper():\n    run()\n", encoding="utf-8")
    return repo


@pytest.fixture()
def wiki_dir(tmp_path: Path) -> Path:
    """Returns an empty wiki directory in a temp path."""
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    return wiki
