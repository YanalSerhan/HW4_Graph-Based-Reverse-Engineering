"""
ArchitecturalBugDetector — identifies structural anti-patterns in the graph.

Detects:
  - Single Points of Failure (SPOFs): nodes whose removal disconnects the graph
  - God-nodes: nodes with excessive cross-community coupling
  - Missing bridges: communities with no shared interface node
  - Communities with external dependency ratio > 0.5
  - OOP misalignment: EXTRACTED call-graph edges that cross class hierarchy boundaries
  - PRD traceability gaps: WHY/TODO/NOTE annotation nodes not connected to impl nodes

Rationale: graph-based detection is far cheaper than full static analysis and
surfaces systemic risks that per-file linters cannot see.
"""

from __future__ import annotations

import concurrent.futures
import logging
from collections.abc import Callable

from ..community_detector import Community
from ..graph_models import Graph
from ..hub_classifier import HubVsBottleneckClassifier
from ..token_counter import TokenCounter
from .base import BaseAgent, LLMStubMixin
from .bug_rules import (
    detect_isolated_communities,
    detect_oop_misalignment,
    detect_prd_traceability_gaps,
    detect_spofs,
)
from .bug_rules_mathsquiz import detect_mathsquiz_logic_bugs
from .bug_rules_syntax import detect_syntax_errors
from .bug_types import ArchitecturalBug

logger = logging.getLogger(__name__)

AGENT_NAME = "ArchitecturalBugDetector"
LLMCallable = Callable[[str], str]


class ArchitecturalBugDetector(BaseAgent, LLMStubMixin):
    """
    Runs structural anti-pattern detection passes over the graph.

    Each detection pass is a separate method, making the class extensible
    without violating Open/Closed — add new passes without modifying existing.
    """

    def __init__(
        self,
        token_counter: TokenCounter,
        llm_call: LLMCallable | None = None,
        token_budget: int = 2000,
    ) -> None:
        super().__init__(token_counter, token_budget)
        self._llm_call = llm_call or self._default_llm_stub
        self._classifier = HubVsBottleneckClassifier()

    def setup(self, graph: Graph, communities: list[Community]) -> tuple[Graph, list[Community]]:
        """Prepares the graph and communities for bug detection passes."""
        return graph, communities

    def process(self, data: tuple[Graph, list[Community]]) -> list[ArchitecturalBug]:
        """Runs all detection passes concurrently and returns consolidated bug list."""
        graph, communities = data
        bugs: list[ArchitecturalBug] = []

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(detect_spofs, graph, communities, self._classifier),
                executor.submit(detect_isolated_communities, communities),
                executor.submit(detect_oop_misalignment, graph),
                executor.submit(detect_prd_traceability_gaps, graph),
                executor.submit(detect_syntax_errors, graph),
                executor.submit(detect_mathsquiz_logic_bugs, graph),
            ]
            for future in concurrent.futures.as_completed(futures):
                bugs.extend(future.result())

        return bugs

    def format_output(self, data: list[ArchitecturalBug]) -> list[ArchitecturalBug]:
        """Formats and logs the final list of architectural bugs."""
        logger.info("%s detected %d architectural issues.", AGENT_NAME, len(data))
        return data
