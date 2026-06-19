"""
inspector_rules.py — higher-level validation rules combining evidence.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from ...constants import EDGE_TYPE_AMBIGUOUS, EDGE_TYPE_INFERRED
from .inspector_helpers import (
    InspectionResult,
    ValidationOutcome,
    build_hub_node_prompt,
    validate_edge,
)

if TYPE_CHECKING:
    from pathlib import Path

    from ..graph_models import Graph, GraphEdge
    from ..token_counter import TokenCounter
    from .graph_analyst import ArchitecturalInsight


def validate_insight(
    insight: ArchitecturalInsight,
    graph: Graph,
    inferred_edges: list[GraphEdge],
    ambiguous_edges: list[GraphEdge],
    repo_path: Path,
    counter: TokenCounter,
    llm_call: Callable[[str], str],
    agent_name: str,
) -> InspectionResult:
    """Validates a single insight, checking relevant INFERRED / AMBIGUOUS edges."""
    from ..token_counter import TokenUsage

    if insight.confidence_level == EDGE_TYPE_AMBIGUOUS:
        return InspectionResult(
            insight_title=insight.title,
            outcome=ValidationOutcome.ESCALATED,
            evidence="AMBIGUOUS edges require human review.",
            edge_type=EDGE_TYPE_AMBIGUOUS,
        )

    hub_prompt = build_hub_node_prompt(insight, graph, repo_path)
    if hub_prompt:
        t_in = counter.estimate_tokens(hub_prompt)
        response = llm_call(hub_prompt)
        t_out = counter.estimate_tokens(response)
        counter.record(TokenUsage(agent_name, t_in, t_out))
        return InspectionResult(
            insight_title=insight.title,
            outcome=ValidationOutcome.CONFIRMED,
            evidence=response,
            edge_type="CODE_INSPECTION",
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

    outcomes = [validate_edge(e, graph, repo_path) for e in related_inferred[:5]]
    confirmed = sum(1 for o in outcomes if o == ValidationOutcome.CONFIRMED)
    final = (
        ValidationOutcome.CONFIRMED if confirmed > len(outcomes) / 2 else ValidationOutcome.DISPUTED
    )
    prompt = f"Verify insight '{insight.title}': {confirmed}/{len(outcomes)} edges confirmed."
    t_in = counter.estimate_tokens(prompt)
    response = llm_call(prompt)
    t_out = counter.estimate_tokens(response)
    counter.record(TokenUsage(agent_name, t_in, t_out))

    return InspectionResult(
        insight_title=insight.title,
        outcome=final,
        evidence=f"{confirmed}/{len(outcomes)} INFERRED edges confirmed by AST.",
        edge_type=EDGE_TYPE_INFERRED,
    )
