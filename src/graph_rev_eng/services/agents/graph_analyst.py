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
from pathlib import Path

from ..community_detector import Community
from ..graph_models import Graph
from ..token_counter import TokenCounter
from .analyst_helpers import analyse_ambiguous_edges, analyse_communities, analyse_hubs
from .analyst_types import ArchitecturalInsight
from .base import BaseAgent, LLMStubMixin

logger = logging.getLogger(__name__)

AGENT_NAME = "GraphAnalystAgent"
LLMCallable = Callable[[str], str]


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
                    analyse_communities,
                    graph,
                    communities,
                    html_content,
                    report_content,
                    self._llm_call,
                    self._counter,
                    AGENT_NAME,
                ),
                executor.submit(
                    analyse_hubs,
                    graph,
                    html_content,
                    report_content,
                    self._llm_call,
                    self._counter,
                    AGENT_NAME,
                ),
                executor.submit(
                    analyse_ambiguous_edges, graph, self._llm_call, self._counter, AGENT_NAME
                ),
            ]
            for future in concurrent.futures.as_completed(futures):
                insights.extend(future.result())

        return insights

    def format_output(self, data: list[ArchitecturalInsight]) -> list[ArchitecturalInsight]:
        """Formats and logs the final list of architectural insights."""
        logger.info("%s produced %d insights.", AGENT_NAME, len(data))
        return data


