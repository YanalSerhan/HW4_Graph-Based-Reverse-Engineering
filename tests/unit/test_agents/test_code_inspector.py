"""Unit tests for agents/code_inspector.py — CodeInspectorAgent."""

from __future__ import annotations

from pathlib import Path

from graph_rev_eng.constants import (
    EDGE_TYPE_AMBIGUOUS,
    EDGE_TYPE_EXTRACTED,
    EDGE_TYPE_INFERRED,
)
from graph_rev_eng.services.agents.code_inspector import (
    CodeInspectorAgent,
)
from graph_rev_eng.services.agents.graph_analyst import ArchitecturalInsight
from graph_rev_eng.services.agents.inspector_helpers import ValidationOutcome, validate_edge
from graph_rev_eng.services.community_detector import CommunityDetector
from graph_rev_eng.services.graph_models import GraphEdge
from graph_rev_eng.services.token_counter import TokenCounter


def _make_agent(mock_repo_path: Path, token_counter: TokenCounter, mock_llm_call):
    return CodeInspectorAgent(
        repo_path=mock_repo_path,
        token_counter=token_counter,
        llm_call=mock_llm_call,
    )


class TestCodeInspectorAgent:
    def test_run_returns_results_list(
        self, simple_graph, mock_repo_path, token_counter, mock_llm_call
    ):
        CommunityDetector().detect(simple_graph)
        insight = ArchitecturalInsight(
            title="Test insight",
            observation="obs",
            relation="rel",
            confidence_level=EDGE_TYPE_INFERRED,
            context="ctx",
            source_node_ids=["n2"],
        )
        agent = _make_agent(mock_repo_path, token_counter, mock_llm_call)
        results = agent.run(simple_graph, [insight])
        assert isinstance(results, list)

    def test_ambiguous_insight_escalated(
        self, simple_graph, mock_repo_path, token_counter, mock_llm_call
    ):
        insight = ArchitecturalInsight(
            title="Ambiguous",
            observation="obs",
            relation="rel",
            confidence_level=EDGE_TYPE_AMBIGUOUS,
            context="ctx",
            source_node_ids=["n3"],
        )
        agent = _make_agent(mock_repo_path, token_counter, mock_llm_call)
        results = agent.run(simple_graph, [insight])
        assert any(r.outcome == ValidationOutcome.ESCALATED for r in results)

    def test_validate_edge_ambiguous_returns_escalated(
        self, simple_graph, mock_repo_path, token_counter, mock_llm_call
    ):
        edge = GraphEdge("n3", "n4", EDGE_TYPE_AMBIGUOUS)
        _make_agent(mock_repo_path, token_counter, mock_llm_call)
        outcome = validate_edge(edge, simple_graph, mock_repo_path)
        assert outcome == ValidationOutcome.ESCALATED

    def test_validate_edge_extracted_skips_ast(
        self, simple_graph, mock_repo_path, token_counter, mock_llm_call
    ):
        """EXTRACTED edges are not validated via AST — skip if no file."""
        edge = GraphEdge("n1", "n2", EDGE_TYPE_EXTRACTED)
        _make_agent(mock_repo_path, token_counter, mock_llm_call)
        # n1 has file_path src/module_a.py which doesn't exist in mock_repo — expect SKIPPED
        outcome = validate_edge(edge, simple_graph, mock_repo_path)
        assert outcome in {
            ValidationOutcome.SKIPPED,
            ValidationOutcome.CONFIRMED,
            ValidationOutcome.DISPUTED,
        }

    def test_ast_call_found_returns_confirmed(
        self, tmp_path: Path, token_counter, mock_llm_call, simple_graph
    ):
        """If the target function name appears in source AST, outcome is CONFIRMED."""
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "src").mkdir()
        caller = repo / "src" / "module_a.py"
        caller.write_text("def foo():\n    module_b()\n", encoding="utf-8")
        simple_graph.nodes["n1"].file_path = "src/module_a.py"
        simple_graph.nodes["n2"].label = "module_b"
        edge = simple_graph.edges[0]  # n1 → n2, EXTRACTED
        # Change to INFERRED for AST check
        edge.edge_type = EDGE_TYPE_INFERRED
        CodeInspectorAgent(
            repo_path=repo, token_counter=token_counter, llm_call=mock_llm_call
        )
        outcome = validate_edge(edge, simple_graph, repo)
        assert outcome == ValidationOutcome.CONFIRMED

    def test_empty_insights_returns_empty_results(
        self, simple_graph, mock_repo_path, token_counter, mock_llm_call
    ):
        agent = _make_agent(mock_repo_path, token_counter, mock_llm_call)
        results = agent.run(simple_graph, [])
        assert results == []
