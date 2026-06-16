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

import ast
import concurrent.futures
import logging
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from ...constants import EDGE_TYPE_AMBIGUOUS, EDGE_TYPE_INFERRED
from ..graph_models import Graph, GraphEdge
from ..token_counter import TokenCounter, TokenUsage
from .base import BaseAgent, LLMStubMixin
from .graph_analyst import ArchitecturalInsight

logger = logging.getLogger(__name__)

AGENT_NAME = "CodeInspectorAgent"
LLMCallable = Callable[[str], str]


class ValidationOutcome(str, Enum):
    """Result of validating an insight against source code."""

    CONFIRMED = "CONFIRMED"
    DISPUTED = "DISPUTED"
    ESCALATED = "ESCALATED"
    SKIPPED = "SKIPPED"


@dataclass
class InspectionResult:
    """Validation outcome for a single ArchitecturalInsight."""

    insight_title: str
    outcome: ValidationOutcome
    evidence: str
    edge_type: str = ""


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
                    self._validate_insight, insight, graph, inferred_edges, ambiguous_edges
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

    def validate_edge(self, edge: GraphEdge, graph: Graph) -> ValidationOutcome:
        """
        Validates a single edge by checking source file AST for the call.

        Returns CONFIRMED if found, DISPUTED if absent, ESCALATED if ambiguous.
        """
        if edge.edge_type == EDGE_TYPE_AMBIGUOUS:
            return ValidationOutcome.ESCALATED

        if edge.label == "semantically_similar_to":
            return self._validate_semantic_duplicate(edge, graph)

        source_node = graph.get_node(edge.source_id)
        target_node = graph.get_node(edge.target_id)
        if not source_node or not target_node:
            return ValidationOutcome.SKIPPED

        source_file = self._repo_path / source_node.file_path
        if not source_file.exists() or source_file.suffix != ".py":
            return ValidationOutcome.SKIPPED

        try:
            found = self._ast_contains_call(source_file, target_node.label)
            return ValidationOutcome.CONFIRMED if found else ValidationOutcome.DISPUTED
        except (SyntaxError, OSError) as exc:
            logger.warning("AST parse error for %s: %s", source_file, exc)
            return ValidationOutcome.SKIPPED

    def _validate_insight(
        self,
        insight: ArchitecturalInsight,
        graph: Graph,
        inferred_edges: list[GraphEdge],
        ambiguous_edges: list[GraphEdge],
    ) -> InspectionResult:
        """Validates a single insight, checking relevant INFERRED / AMBIGUOUS edges."""
        if insight.confidence_level == EDGE_TYPE_AMBIGUOUS:
            return InspectionResult(
                insight_title=insight.title,
                outcome=ValidationOutcome.ESCALATED,
                evidence="AMBIGUOUS edges require human review.",
                edge_type=EDGE_TYPE_AMBIGUOUS,
            )

        related_inferred = [
            e
            for e in inferred_edges
            if e.source_id in insight.source_node_ids or e.target_id in insight.source_node_ids
        ]

        if not related_inferred:
            return InspectionResult(
                insight_title=insight.title,
                outcome=ValidationOutcome.SKIPPED,
                evidence="No INFERRED edges linked to this insight's source nodes.",
            )

        outcomes = [self.validate_edge(e, graph) for e in related_inferred[:5]]
        confirmed = sum(1 for o in outcomes if o == ValidationOutcome.CONFIRMED)
        final = (
            ValidationOutcome.CONFIRMED
            if confirmed > len(outcomes) / 2
            else ValidationOutcome.DISPUTED
        )
        prompt = f"Verify insight '{insight.title}': {confirmed}/{len(outcomes)} edges confirmed."
        t_in = self._counter.estimate_tokens(prompt)
        response = self._llm_call(prompt)
        t_out = self._counter.estimate_tokens(response)
        self._counter.record(TokenUsage(AGENT_NAME, t_in, t_out))

        return InspectionResult(
            insight_title=insight.title,
            outcome=final,
            evidence=f"{confirmed}/{len(outcomes)} INFERRED edges confirmed by AST.",
            edge_type=EDGE_TYPE_INFERRED,
        )

    def _ast_contains_call(self, source_file: Path, target_label: str) -> bool:
        """Returns True if target_label appears as a function call in source_file AST."""
        tree = ast.parse(source_file.read_text(encoding="utf-8", errors="replace"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                name = ""
                if isinstance(func, ast.Name):
                    name = func.id
                elif isinstance(func, ast.Attribute):
                    name = func.attr
                if name == target_label:
                    return True
        return False

    def _validate_semantic_duplicate(self, edge: GraphEdge, graph: Graph) -> ValidationOutcome:
        """
        Validates whether semantically similar nodes are actually duplicates.

        Before flagging as duplicates, verify call sites, consumers, tests, and purpose.
        Never recommend merge based on semantic similarity alone.
        """
        source_node = graph.get_node(edge.source_id)
        target_node = graph.get_node(edge.target_id)
        if not source_node or not target_node:
            return ValidationOutcome.SKIPPED

        # Mock check: in reality, we'd use AST to find if they share the same consumers
        # or if they are covered by different tests indicating different purposes.
        # For now, we defensively return DISPUTED to prevent accidental merges
        # based purely on semantic similarity.
        logger.info(
            "SemanticDuplicateValidator: Node '%s' and '%s' are semantically similar. "
            "Defensively disputing merge until call sites and tests are verified.",
            source_node.label,
            target_node.label,
        )
        return ValidationOutcome.DISPUTED
