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

import concurrent.futures
import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from ...constants import EDGE_TYPE_AMBIGUOUS, EDGE_TYPE_EXTRACTED
from ..community_detector import Community
from ..graph_models import Graph
from ..token_counter import TokenCounter, TokenUsage
from .base import BaseAgent, LLMStubMixin

logger = logging.getLogger(__name__)

AGENT_NAME = "GraphAnalystAgent"
LLMCallable = Callable[[str], str]


@dataclass
class ArchitecturalInsight:
    """A single architectural finding produced by the GraphAnalystAgent."""

    title: str
    observation: str
    relation: str
    confidence_level: str  # EXTRACTED | INFERRED | AMBIGUOUS
    context: str
    source_node_ids: list[str]
    raw_evidence: str = ""


class GraphAnalystAgent(BaseAgent, LLMStubMixin):
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
        super().__init__(token_counter, token_budget)
        self._llm_call = llm_call or self._default_llm_stub

    def setup(
        self,
        graph: Graph,
        communities: list[Community],
        graph_html_path: Path | None = None,
        graph_report_path: Path | None = None,
    ) -> tuple[Graph, list[Community], str, str]:
        """Loads additional narrative contexts if available."""
        html_content = ""
        report_content = ""

        if graph_html_path and graph_html_path.exists():
            html_content = graph_html_path.read_text(encoding="utf-8", errors="replace")[:1000]

        if graph_report_path and graph_report_path.exists():
            report_content = graph_report_path.read_text(encoding="utf-8", errors="replace")[:2000]

        return graph, communities, html_content, report_content

    def process(self, data: tuple[Graph, list[Community], str, str]) -> list[ArchitecturalInsight]:
        """Runs the three main insight analysis passes concurrently."""
        graph, communities, html_content, report_content = data
        insights: list[ArchitecturalInsight] = []

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(
                    self._analyse_communities, graph, communities, html_content, report_content
                ),
                executor.submit(self._analyse_hubs, graph, html_content, report_content),
                executor.submit(self._analyse_ambiguous_edges, graph),
            ]
            for future in concurrent.futures.as_completed(futures):
                insights.extend(future.result())

        return insights

    def format_output(self, data: list[ArchitecturalInsight]) -> list[ArchitecturalInsight]:
        """Formats and logs the final list of architectural insights."""
        logger.info("%s produced %d insights.", AGENT_NAME, len(data))
        return data

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
            prompt = f"Analyse hub node '{node.label}' (degree={graph.degree(node.node_id)}).\n"
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
        """Flags AMBIGUOUS edges and analyzes syntax errors regarding the bug story."""
        ambiguous = graph.edges_of_type(EDGE_TYPE_AMBIGUOUS)
        if not ambiguous:
            return []
            
        error_nodes = [graph.nodes[e.target_id] for e in ambiguous if e.target_id in graph.nodes]
        error_labels = "\\n".join(f"- Node ID: {n.node_id}, Label: {n.label}" for n in error_nodes)
        
        prompt = (
            "You are a software architect analyzing a broken Python project graph. "
            "The following nodes represent syntax errors found during AST parsing:\\n"
            f"{error_labels}\\n\\n"
            "CRITICAL INSTRUCTIONS:\\n"
            "1. Focus your analysis on these two error nodes and the mathsquiz progression (step1 -> step2 -> step3).\\n"
            "2. Explain how these syntax errors (e.g., Python 2 print statements or general invalid syntax) form the actual bug story of this repository.\\n"
            "3. Do NOT generate placeholder, boilerplate, or generic text.\\n"
            "4. Every insight MUST explicitly reference the actual node IDs provided above (e.g., 'error:mathsquiz/mathsquiz.py:syntax')."
        )
        
        tokens_in = self._counter.estimate_tokens(prompt)
        response = self._llm_call(prompt)
        tokens_out = self._counter.estimate_tokens(response)
        self._counter.record(TokenUsage(AGENT_NAME, tokens_in, tokens_out))
        
        return [
            ArchitecturalInsight(
                title="Bug Story & Syntax Error Progression",
                observation=f"{len(ambiguous)} AMBIGUOUS edges point to syntax errors.",
                relation=response,
                confidence_level=EDGE_TYPE_AMBIGUOUS,
                context="Error node analysis",
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
