from pathlib import Path

from graph_rev_eng.constants import EDGE_TYPE_AMBIGUOUS
from graph_rev_eng.services.agents.graph_analyst import ArchitecturalInsight
from graph_rev_eng.services.agents.inspector_helpers import (
    ValidationOutcome,
    ast_contains_call,
    build_hub_node_prompt,
    validate_edge,
    validate_semantic_duplicate,
)
from graph_rev_eng.services.graph_models import Graph, GraphEdge, GraphNode


def test_ast_contains_call_attribute(tmp_path):
    f = tmp_path / "test.py"
    f.write_text("obj.my_func()", encoding="utf-8")
    assert ast_contains_call(f, "my_func")
    assert not ast_contains_call(f, "other_func")

def test_validate_semantic_duplicate():
    graph = Graph()
    edge = GraphEdge(
        source_id="n1", target_id="n2", edge_type="INFERRED", label="semantically_similar_to"
    )
    assert validate_semantic_duplicate(edge, graph) == ValidationOutcome.SKIPPED

    n1 = GraphNode(node_id="n1", node_type="module", label="a")
    n2 = GraphNode(node_id="n2", node_type="module", label="b")
    graph.nodes["n1"] = n1
    graph.nodes["n2"] = n2

    assert validate_semantic_duplicate(edge, graph) == ValidationOutcome.DISPUTED

def test_build_hub_node_prompt(tmp_path):
    repo = tmp_path
    f = repo / "hub.py"
    f.write_text("def hub(): pass", encoding="utf-8")

    graph = Graph()
    n = GraphNode(node_id="n1", node_type="module", label="hub", file_path="hub.py")
    graph.nodes["n1"] = n

    insight = ArchitecturalInsight(
        title="Hub: test",
        observation="",
        relation="",
        confidence_level="INFERRED",
        context="",
        source_node_ids=["n1"],
    )
    prompt = build_hub_node_prompt(insight, graph, repo)
    assert prompt is not None
    assert "You are the CodeInspectorAgent" in prompt
    assert "def hub(): pass" in prompt

def test_validate_edge_ambiguous():
    edge = GraphEdge(source_id="n1", target_id="n2", edge_type=EDGE_TYPE_AMBIGUOUS)
    assert validate_edge(edge, Graph(), Path()) == ValidationOutcome.ESCALATED

def test_validate_edge_semantic_duplicate():
    edge = GraphEdge(
        source_id="n1", target_id="n2", edge_type="INFERRED", label="semantically_similar_to"
    )
    assert validate_edge(edge, Graph(), Path()) == ValidationOutcome.SKIPPED

def test_validate_edge_missing_nodes():
    edge = GraphEdge(source_id="n1", target_id="n2", edge_type="EXTRACTED")
    assert validate_edge(edge, Graph(), Path()) == ValidationOutcome.SKIPPED

def test_validate_edge_exception(tmp_path):
    f = tmp_path / "bad.py"
    f.write_text("def bad(", encoding="utf-8")

    graph = Graph()
    n1 = GraphNode(node_id="n1", node_type="module", label="n1", file_path="bad.py")
    n2 = GraphNode(node_id="n2", node_type="module", label="target")
    graph.nodes["n1"] = n1
    graph.nodes["n2"] = n2

    edge = GraphEdge(source_id="n1", target_id="n2", edge_type="EXTRACTED")
    assert validate_edge(edge, graph, tmp_path) == ValidationOutcome.SKIPPED
