"""
bug_rules.py — standalone detection rules for architectural bugs.
"""

from __future__ import annotations

from ...constants import EDGE_TYPE_EXTRACTED
from ..community_detector import Community
from ..graph_models import Graph
from ..hub_classifier import HubVsBottleneckClassifier, NodeClassification
from .bug_types import ArchitecturalBug, BugSeverity

HIGH_EXTERNAL_RATIO = 0.5


def detect_spofs(
    graph: Graph, communities: list[Community], classifier: HubVsBottleneckClassifier
) -> list[ArchitecturalBug]:
    """Detects god-nodes and SPOFs via HubVsBottleneckClassifier."""
    reports = classifier.classify(graph, communities)
    risky = classifier.spof_nodes(reports)
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


def detect_isolated_communities(communities: list[Community]) -> list[ArchitecturalBug]:
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


def detect_oop_misalignment(graph: Graph) -> list[ArchitecturalBug]:
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


def detect_prd_traceability_gaps(graph: Graph) -> list[ArchitecturalBug]:
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
