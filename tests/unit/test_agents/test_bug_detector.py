"""Unit tests for agents/bug_detector.py — ArchitecturalBugDetector."""

from __future__ import annotations

import pytest

from src.graph_rev_eng.services.agents.bug_detector import (
    ArchitecturalBugDetector,
    ArchitecturalBug,
    BugSeverity,
)
from src.graph_rev_eng.services.community_detector import CommunityDetector, Community
from src.graph_rev_eng.services.graph_models import Graph, GraphEdge, GraphNode
from src.graph_rev_eng.services.token_counter import TokenCounter
from src.graph_rev_eng.constants import EDGE_TYPE_EXTRACTED, EDGE_TYPE_INFERRED


class TestArchitecturalBugDetector:
    def test_run_returns_list(self, simple_graph, token_counter, mock_llm_call):
        communities = CommunityDetector().detect(simple_graph)
        detector = ArchitecturalBugDetector(token_counter, llm_call=mock_llm_call)
        bugs = detector.run(simple_graph, communities)
        assert isinstance(bugs, list)

    def test_empty_graph_no_bugs(self, empty_graph, token_counter, mock_llm_call):
        detector = ArchitecturalBugDetector(token_counter, llm_call=mock_llm_call)
        bugs = detector.run(empty_graph, [])
        assert bugs == []

    def test_prd_gap_detected(self, token_counter, mock_llm_call):
        """A TODO node with no outgoing edges should be flagged."""
        graph = Graph(
            nodes={"todo": GraphNode("todo", "TODO_implement_feature", "module", "src/todo.py")},
            edges=[],
        )
        detector = ArchitecturalBugDetector(token_counter, llm_call=mock_llm_call)
        bugs = detector.run(graph, [])
        prd_bugs = [b for b in bugs if b.bug_type == "PRD_TRACEABILITY_GAP"]
        assert len(prd_bugs) == 1
        assert prd_bugs[0].severity == BugSeverity.MEDIUM

    def test_oop_misalignment_detected(self, token_counter, mock_llm_call):
        """Nodes in the same file but different communities → OOP fragmentation."""
        graph = Graph(
            nodes={
                "a": GraphNode("a", "ClassA", "class", "src/models.py", community_id=0),
                "b": GraphNode("b", "ClassB", "class", "src/models.py", community_id=1),
            },
            edges=[GraphEdge("a", "b", EDGE_TYPE_EXTRACTED)],
        )
        communities = [Community(0, ["a"]), Community(1, ["b"])]
        detector = ArchitecturalBugDetector(token_counter, llm_call=mock_llm_call)
        bugs = detector.run(graph, communities)
        oop_bugs = [b for b in bugs if b.bug_type == "OOP_HIERARCHY_FRAGMENTATION"]
        assert len(oop_bugs) >= 1

    def test_excessive_external_coupling(self, token_counter, mock_llm_call):
        """Community with > 50% external edges → EXCESSIVE_EXTERNAL_COUPLING."""
        graph = Graph(
            nodes={
                "a": GraphNode("a", "A", "module", "src/a.py"),
                "b": GraphNode("b", "B", "module", "src/b.py"),
                "c": GraphNode("c", "C", "module", "src/c.py"),
            },
            edges=[
                GraphEdge("a", "b", EDGE_TYPE_EXTRACTED),
                GraphEdge("a", "c", EDGE_TYPE_EXTRACTED),
            ],
        )
        communities = [
            Community(0, ["a"], internal_edge_count=0, external_edge_count=3),
        ]
        detector = ArchitecturalBugDetector(token_counter, llm_call=mock_llm_call)
        bugs = detector.run(graph, communities)
        coupling_bugs = [b for b in bugs if b.bug_type == "EXCESSIVE_EXTERNAL_COUPLING"]
        assert len(coupling_bugs) >= 1

    def test_bug_has_recommendation(self, token_counter, mock_llm_call):
        graph = Graph(
            nodes={"note": GraphNode("note", "NOTE_auth_flow", "module", "src/note.py")},
            edges=[],
        )
        detector = ArchitecturalBugDetector(token_counter, llm_call=mock_llm_call)
        bugs = detector.run(graph, [])
        for bug in bugs:
            assert bug.recommendation != ""
