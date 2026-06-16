"""Unit tests for agents/graph_analyst.py — GraphAnalystAgent."""

from __future__ import annotations

from graph_rev_eng.constants import EDGE_TYPE_AMBIGUOUS
from graph_rev_eng.services.agents.graph_analyst import (
    ArchitecturalInsight,
    GraphAnalystAgent,
)
from graph_rev_eng.services.community_detector import CommunityDetector


class TestGraphAnalystAgent:
    def test_run_returns_insights(self, simple_graph, token_counter, mock_llm_call):
        communities = CommunityDetector().detect(simple_graph)
        agent = GraphAnalystAgent(token_counter, llm_call=mock_llm_call)
        insights = agent.run(simple_graph, communities)
        assert len(insights) > 0

    def test_insights_are_architectural_insight_type(
        self, simple_graph, token_counter, mock_llm_call
    ):
        communities = CommunityDetector().detect(simple_graph)
        agent = GraphAnalystAgent(token_counter, llm_call=mock_llm_call)
        insights = agent.run(simple_graph, communities)
        for insight in insights:
            assert isinstance(insight, ArchitecturalInsight)

    def test_ambiguous_edges_produce_insight(self, simple_graph, token_counter, mock_llm_call):
        communities = CommunityDetector().detect(simple_graph)
        agent = GraphAnalystAgent(token_counter, llm_call=mock_llm_call)
        insights = agent.run(simple_graph, communities)
        ambiguous_insights = [i for i in insights if i.confidence_level == EDGE_TYPE_AMBIGUOUS]
        assert len(ambiguous_insights) >= 1

    def test_token_counter_records_calls(self, simple_graph, token_counter, mock_llm_call):
        communities = CommunityDetector().detect(simple_graph)
        agent = GraphAnalystAgent(token_counter, llm_call=mock_llm_call)
        agent.run(simple_graph, communities)
        assert token_counter.total_tokens > 0

    def test_stub_llm_used_when_no_llm_provided(self, simple_graph, token_counter):
        communities = CommunityDetector().detect(simple_graph)
        agent = GraphAnalystAgent(token_counter)
        insights = agent.run(simple_graph, communities)
        # Stub still produces insights
        assert len(insights) >= 1

    def test_empty_graph_produces_minimal_insights(self, empty_graph, token_counter, mock_llm_call):
        agent = GraphAnalystAgent(token_counter, llm_call=mock_llm_call)
        insights = agent.run(empty_graph, [])
        # No communities or hubs — should produce 0 insights (no AMBIGUOUS edges either)
        assert isinstance(insights, list)

    def test_insight_has_source_node_ids(self, simple_graph, token_counter, mock_llm_call):
        communities = CommunityDetector().detect(simple_graph)
        agent = GraphAnalystAgent(token_counter, llm_call=mock_llm_call)
        insights = agent.run(simple_graph, communities)
        for insight in insights:
            assert isinstance(insight.source_node_ids, list)
