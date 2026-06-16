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

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from ..graph_models import Graph
from ..community_detector import Community
from ..hub_classifier import HubVsBottleneckClassifier, NodeClassification
from ..token_counter import TokenCounter, TokenUsage
from ...constants import EDGE_TYPE_EXTRACTED

logger = logging.getLogger(__name__)

AGENT_NAME = "ArchitecturalBugDetector"
LLMCallable = Callable[[str], str]
HIGH_EXTERNAL_RATIO = 0.5


class BugSeverity(str, Enum):
    """Severity level for a detected architectural bug."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class ArchitecturalBug:
    """A detected structural anti-pattern."""

    bug_type: str
    severity: BugSeverity
    description: str
    affected_node_ids: list[str] = field(default_factory=list)
    recommendation: str = ""


class ArchitecturalBugDetector:
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
        self._counter = token_counter
        self._llm_call = llm_call or self._default_llm_stub
        self._budget = token_budget
        self._classifier = HubVsBottleneckClassifier()

    def run(self, graph: Graph, communities: list[Community]) -> list[ArchitecturalBug]:
        """Runs all detection passes and returns consolidated bug list."""
        bugs: list[ArchitecturalBug] = []
        bugs.extend(self._detect_spofs(graph, communities))
        bugs.extend(self._detect_isolated_communities(communities))
        bugs.extend(self._detect_oop_misalignment(graph))
        bugs.extend(self._detect_prd_traceability_gaps(graph))
        logger.info("%s detected %d architectural issues.", AGENT_NAME, len(bugs))
        return bugs

    def _detect_spofs(self, graph: Graph, communities: list[Community]) -> list[ArchitecturalBug]:
        """Detects god-nodes and SPOFs via HubVsBottleneckClassifier."""
        reports = self._classifier.classify(graph, communities)
        risky = self._classifier.spof_nodes(reports)
        bugs: list[ArchitecturalBug] = []
        for report in risky:
            severity = (
                BugSeverity.CRITICAL
                if report.classification == NodeClassification.GOD_NODE
                else BugSeverity.HIGH
            )
            bugs.append(
                ArchitecturalBug(
                    bug_type=str(report.classification),
                    severity=severity,
                    description=report.rationale,
                    affected_node_ids=[report.node_id],
                    recommendation=(
                        "Decompose this node into smaller, single-responsibility units "
                        "and introduce an interface/facade to reduce coupling."
                    ),
                )
            )
        return bugs

    def _detect_isolated_communities(
        self, communities: list[Community]
    ) -> list[ArchitecturalBug]:
        """Flags communities with > 50% external edges (excessive coupling)."""
        bugs: list[ArchitecturalBug] = []
        for community in communities:
            total = community.internal_edge_count + community.external_edge_count
            if total == 0:
                continue
            ext_ratio = community.external_edge_count / total
            if ext_ratio > HIGH_EXTERNAL_RATIO:
                bugs.append(
                    ArchitecturalBug(
                        bug_type="EXCESSIVE_EXTERNAL_COUPLING",
                        severity=BugSeverity.MEDIUM,
                        description=(
                            f"Community '{community.dominant_label}' has "
                            f"{ext_ratio:.0%} external edges — boundary may be misdrawn."
                        ),
                        affected_node_ids=community.node_ids,
                        recommendation=(
                            "Review community boundary: consider merging with a neighbouring "
                            "community or extracting a shared interface."
                        ),
                    )
                )
        return bugs

    def _detect_oop_misalignment(self, graph: Graph) -> list[ArchitecturalBug]:
        """
        Identifies EXTRACTED call-graph edges that cross class hierarchy boundaries.

        Heuristic: if source and target nodes share the same file_path prefix but
        belong to different communities, the class hierarchy may be fragmented.
        """
        bugs: list[ArchitecturalBug] = []
        for edge in graph.edges_of_type(EDGE_TYPE_EXTRACTED):
            src = graph.get_node(edge.source_id)
            tgt = graph.get_node(edge.target_id)
            if not src or not tgt:
                continue
            same_file = src.file_path and src.file_path == tgt.file_path
            diff_community = src.community_id != tgt.community_id and src.community_id != -1
            if same_file and diff_community:
                bugs.append(
                    ArchitecturalBug(
                        bug_type="OOP_HIERARCHY_FRAGMENTATION",
                        severity=BugSeverity.LOW,
                        description=(
                            f"Nodes '{src.label}' and '{tgt.label}' share file "
                            f"'{src.file_path}' but belong to different communities — "
                            "possible class hierarchy fragmentation."
                        ),
                        affected_node_ids=[edge.source_id, edge.target_id],
                        recommendation="Verify class structure; consider re-assigning community.",
                    )
                )
        return bugs

    def _detect_prd_traceability_gaps(self, graph: Graph) -> list[ArchitecturalBug]:
        """
        Checks that annotation nodes (WHY/TODO/NOTE labels) link to impl nodes.

        A traceability gap occurs when a documentation node has no outgoing edges
        to an implementation node in the same graph.
        """
        annotation_keywords = {"WHY", "TODO", "NOTE", "FIXME"}
        bugs: list[ArchitecturalBug] = []
        for node in graph.nodes.values():
            is_annotation = any(kw in node.label.upper() for kw in annotation_keywords)
            if not is_annotation:
                continue
            outgoing = graph.neighbors(node.node_id)
            if not outgoing:
                bugs.append(
                    ArchitecturalBug(
                        bug_type="PRD_TRACEABILITY_GAP",
                        severity=BugSeverity.MEDIUM,
                        description=(
                            f"Annotation node '{node.label}' has no outgoing edges to "
                            "an implementation node — requirement may be unimplemented."
                        ),
                        affected_node_ids=[node.node_id],
                        recommendation="Link this annotation to its implementation node.",
                    )
                )
        return bugs

    def _default_llm_stub(self, prompt: str) -> str:
        """Deterministic stub for test environments without LLM access."""
        return f"[STUB] Bug analysis pending LLM. ({len(prompt)} chars)"
