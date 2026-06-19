"""
analyst_helpers.py — analysis logic for GraphAnalystAgent.
"""
from __future__ import annotations

from collections.abc import Callable

from ...constants import EDGE_TYPE_AMBIGUOUS, EDGE_TYPE_EXTRACTED
from ..community_detector import Community
from ..graph_models import Graph
from ..token_counter import TokenCounter, TokenUsage
from .analyst_types import ArchitecturalInsight

LLMCallable = Callable[[str], str]


def analyse_communities(
    graph: Graph,
    communities: list[Community],
    html_content: str,
    report_content: str,
    llm_call: LLMCallable,
    counter: TokenCounter,
    agent_name: str,
) -> list[ArchitecturalInsight]:
    """Generates one insight per detected community."""
    results: list[ArchitecturalInsight] = []
    for community in communities:
        prompt = _community_prompt(graph, community, html_content, report_content)
        tokens_in = counter.estimate_tokens(prompt)
        response = llm_call(prompt)
        tokens_out = counter.estimate_tokens(response)
        counter.record(TokenUsage(agent_name, tokens_in, tokens_out))
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


def analyse_hubs(
    graph: Graph,
    html_content: str,
    report_content: str,
    llm_call: LLMCallable,
    counter: TokenCounter,
    agent_name: str,
) -> list[ArchitecturalInsight]:
    """Generates insights for nodes with degree ≥ 5 (architectural hubs)."""
    results: list[ArchitecturalInsight] = []
    hub_nodes = [n for n in graph.nodes.values() if graph.degree(n.node_id) >= 5]
    for node in hub_nodes[:10]:  # cap at 10 to respect budget
        prompt = f"Analyse hub node '{node.label}' (degree={graph.degree(node.node_id)}).\n"
        if report_content:
            prompt += f"Consider this narrative context:\n{report_content[:500]}\n"
        tokens_in = counter.estimate_tokens(prompt)
        response = llm_call(prompt)
        tokens_out = counter.estimate_tokens(response)
        counter.record(TokenUsage(agent_name, tokens_in, tokens_out))
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


def analyse_ambiguous_edges(
    graph: Graph,
    llm_call: LLMCallable,
    counter: TokenCounter,
    agent_name: str,
) -> list[ArchitecturalInsight]:
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
        "1. Focus your analysis on these two error nodes and the mathsquiz progression "
        "(step1 -> step2 -> step3).\\n"
        "2. Explain how these syntax errors (e.g., Python 2 print statements or general "
        "invalid syntax) form the actual bug story of this repository.\\n"
        "3. Do NOT generate placeholder, boilerplate, or generic text.\\n"
        "4. Every insight MUST explicitly reference the actual node IDs provided above "
        "(e.g., 'error:mathsquiz/mathsquiz.py:syntax')."
    )

    tokens_in = counter.estimate_tokens(prompt)
    response = llm_call(prompt)
    tokens_out = counter.estimate_tokens(response)
    counter.record(TokenUsage(agent_name, tokens_in, tokens_out))

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
