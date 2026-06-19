"""
CodeInspectorAgent — validates graph-inferred insights against source code.

Rationale: the graph is a model of the code, not the code itself. INFERRED
and AMBIGUOUS edges are hypotheses that must be verified. This agent is the
ground-truth arbiter — it reads actual Python source files and confirms or
disputes each architectural insight produced by the GraphAnalystAgent.

Validation outcomes:
  - CONFIRMED  : source code evidence matches the inferred relationship
  - DISPUTED   : source code contradicts the inference
  - ESCALATED  : AMBIGUOUS edge flagged for human review
"""

from __future__ import annotations

import concurrent.futures
import logging
from collections.abc import Callable
from pathlib import Path

from ...constants import EDGE_TYPE_AMBIGUOUS, EDGE_TYPE_INFERRED
from ..graph_models import Graph, GraphEdge
from ..token_counter import TokenCounter
from .base import BaseAgent, LLMStubMixin
from .graph_analyst import ArchitecturalInsight
from .inspector_helpers import InspectionResult
from .inspector_rules import validate_insight

logger = logging.getLogger(__name__)

AGENT_NAME = "CodeInspectorAgent"
LLMCallable = Callable[[str], str]


class CodeInspectorAgent(BaseAgent, LLMStubMixin):
    """
    Validates graph insights by inspecting actual Python source files.

    For each INFERRED edge in the graph, attempts to find call-site evidence
    in the source AST.  AMBIGUOUS edges are escalated without AST check.
    """

    def __init__(
        self,
        repo_path: Path,
        token_counter: TokenCounter,
        llm_call: LLMCallable | None = None,
        token_budget: int = 2000,
    ) -> None:
        super().__init__(token_counter, token_budget)
        self._repo_path = repo_path
        self._llm_call = llm_call or self._default_llm_stub

    def setup(
        self, graph: Graph, insights: list[ArchitecturalInsight]
    ) -> tuple[Graph, list[ArchitecturalInsight], list[GraphEdge], list[GraphEdge]]:
        """Extracts necessary edge lists from the graph before processing."""
        inferred_edges = graph.edges_of_type(EDGE_TYPE_INFERRED)
        ambiguous_edges = graph.edges_of_type(EDGE_TYPE_AMBIGUOUS)
        return graph, insights, inferred_edges, ambiguous_edges

    def process(
        self,
        data: tuple[Graph, list[ArchitecturalInsight], list[GraphEdge], list[GraphEdge]],
    ) -> list[InspectionResult]:
        """Validates insights concurrently using a thread pool."""
        graph, insights, inferred_edges, ambiguous_edges = data
        results: list[InspectionResult] = []

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(
                    validate_insight,
                    insight,
                    graph,
                    inferred_edges,
                    ambiguous_edges,
                    self._repo_path,
                    self._counter,
                    self._llm_call,
                    AGENT_NAME,
                )
                for insight in insights
            ]
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())

        return results

    def format_output(self, data: list[InspectionResult]) -> list[InspectionResult]:
        """Formats and logs the final results."""
        logger.info("%s produced %d inspection results.", AGENT_NAME, len(data))
        return data
