"""
GraphAnalystAgent — extracts architectural insights using a five-step pipeline.

Five-step inference pipeline (from lecture):
  1. Observe   — enumerate structural facts directly visible in the graph
  2. Relate    — identify relationships between observed facts
  3. Confidence — assign confidence level (Extracted / Inferred / Ambiguous)
  4. Context   — place findings in architectural context (layer, community)
  5. Source    — trace every claim back to a specific node/edge in graph.json

Rationale: making the pipeline explicit prevents agents from confusing
observation (what the graph shows) with inference (what it implies). This
distinction is critical for the CodeInspector to validate findings later.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from ..graph_models import Graph
from ..community_detector import Community
from ..token_counter import TokenCounter, TokenUsage
from ...constants import EDGE_TYPE_EXTRACTED, EDGE_TYPE_INFERRED, EDGE_TYPE_AMBIGUOUS

logger = logging.getLogger(__name__)

AGENT_NAME = "GraphAnalystAgent"


@dataclass
class ArchitecturalInsight:
    """A single architectural finding produced by the GraphAnalystAgent."""

    title: str
    observation: str
    relation: str
    confidence_level: str   # EXTRACTED | INFERRED | AMBIGUOUS
    context: str
    source_node_ids: list[str]
    raw_evidence: str = ""


# Type alias for an injectable LLM call (keeps agents testable without a key)
LLMCallable = Callable[[str], str]


class GraphAnalystAgent:
    """
    Reads the graph and community map, applies the five-step pipeline,
    and returns a list of ArchitecturalInsights.

    The LLM callable is injected so tests can substitute a deterministic stub
    while production wires in the real ApiGatekeeper.execute() call.
    """

    def __init__(
        self,
        token_counter: TokenCounter,
        llm_call: LLMCallable | None = None,
        token_budget: int = 2000,
    ) -> None:
        self._counter = token_counter
        self._llm_call = llm_call or self._default_llm_stub
        self._budget = token_budget

    def run(
        self, 
        graph: Graph, 
        communities: list[Community],
        graph_html_path: Path | None = None,
        graph_report_path: Path | None = None,
    ) -> list[ArchitecturalInsight]:
        """
        Executes the five-step pipeline and returns extracted insights.
        Implements the three-source reading protocol using graph.json (Graph), 
        graph.html, and GRAPH_REPORT.md.
        """
        html_content = ""
        report_content = ""
        
        if graph_html_path and graph_html_path.exists():
            html_content = graph_html_path.read_text(encoding="utf-8", errors="replace")[:1000]
            
        if graph_report_path and graph_report_path.exists():
            report_content = graph_report_path.read_text(encoding="utf-8", errors="replace")[:2000]

        insights: list[ArchitecturalInsight] = []
        insights.extend(self._analyse_communities(graph, communities, html_content, report_content))
        insights.extend(self._analyse_hubs(graph, html_content, report_content))
        insights.extend(self._analyse_ambiguous_edges(graph))
        logger.info("%s produced %d insights.", AGENT_NAME, len(insights))
        return insights

    def _analyse_communities(
        self, 
        graph: Graph, 
        communities: list[Community],
        html_content: str = "",
        report_content: str = "",
    ) -> list[ArchitecturalInsight]:
        """Generates one insight per detected community."""
        results: list[ArchitecturalInsight] = []
        for community in communities:
            prompt = self._community_prompt(graph, community, html_content, report_content)
            tokens_in = self._counter.estimate_tokens(prompt)
            response = self._llm_call(prompt)
            tokens_out = self._counter.estimate_tokens(response)
            self._counter.record(TokenUsage(AGENT_NAME, tokens_in, tokens_out))
            results.append(
                ArchitecturalInsight(
                    title=f"Community: {community.dominant_label}",
                    observation=f"Community of {community.size} nodes with "
                                f"{community.cohesion_ratio:.0%} cohesion.",
                    relation=response,
                    confidence_level=EDGE_TYPE_EXTRACTED,
                    context=f"Community ID {community.community_id}",
                    source_node_ids=community.node_ids[:5],
                )
            )
        return results

    def _analyse_hubs(
        self, 
        graph: Graph,
        html_content: str = "",
        report_content: str = "",
    ) -> list[ArchitecturalInsight]:
        """Generates insights for nodes with degree ≥ 5 (architectural hubs)."""
        results: list[ArchitecturalInsight] = []
        hub_nodes = [n for n in graph.nodes.values() if graph.degree(n.node_id) >= 5]
        for node in hub_nodes[:10]:  # cap at 10 to respect budget
            prompt = (
                f"Analyse hub node '{node.label}' (degree={graph.degree(node.node_id)}).\n"
            )
            if report_content:
                prompt += f"Consider this narrative context:\n{report_content[:500]}\n"
            tokens_in = self._counter.estimate_tokens(prompt)
            response = self._llm_call(prompt)
            tokens_out = self._counter.estimate_tokens(response)
            self._counter.record(TokenUsage(AGENT_NAME, tokens_in, tokens_out))
            results.append(
                ArchitecturalInsight(
                    title=f"Hub: {node.label}",
                    observation=f"Node '{node.label}' has degree {graph.degree(node.node_id)}.",
                    relation=response,
                    confidence_level=EDGE_TYPE_EXTRACTED,
                    context=f"File: {node.file_path}",
                    source_node_ids=[node.node_id],
                )
            )
        return results

    def _analyse_ambiguous_edges(self, graph: Graph) -> list[ArchitecturalInsight]:
        """Flags AMBIGUOUS edges for human review via the CodeInspector."""
        ambiguous = graph.edges_of_type(EDGE_TYPE_AMBIGUOUS)
        if not ambiguous:
            return []
        return [
            ArchitecturalInsight(
                title="Ambiguous Edges Detected",
                observation=f"{len(ambiguous)} AMBIGUOUS edges require validation.",
                relation="Recommend CodeInspectorAgent review each edge against source code.",
                confidence_level=EDGE_TYPE_AMBIGUOUS,
                context="Entire graph",
                source_node_ids=list({e.source_id for e in ambiguous}),
            )
        ]

    def _community_prompt(
        self, 
        graph: Graph, 
        community: Community,
        html_content: str = "",
        report_content: str = "",
    ) -> str:
        """Builds the LLM prompt for community analysis."""
        node_labels = [
            graph.nodes[nid].label for nid in community.node_ids[:10] if nid in graph.nodes
        ]
        prompt = (
            f"You are a software architect. Analyse this code community:\n"
            f"Name: {community.dominant_label}\n"
            f"Size: {community.size} nodes\n"
            f"Cohesion: {community.cohesion_ratio:.0%}\n"
            f"Key nodes: {', '.join(node_labels)}\n"
        )
        if report_content:
            prompt += f"\nNarrative Report Context:\n{report_content[:500]}\n"
        if html_content:
            prompt += f"\nGraph HTML Metadata (excerpt):\n{html_content[:200]}\n"
            
        prompt += "\nWhat is the dominant architectural responsibility of this community?"
        return prompt

    def _default_llm_stub(self, prompt: str) -> str:
        """
        Deterministic stub used when no real LLM is configured.

        Returns a structured placeholder that downstream agents can parse
        without failing, enabling full pipeline testing without API keys.
        """
        return (
            "[STUB] Architectural analysis pending LLM configuration. "
            f"Prompt length: {len(prompt)} chars."
        )
