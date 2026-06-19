"""
report_formatter.py — markdown formatting helpers for ReportWriterAgent.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from .bug_types import BugSeverity

if TYPE_CHECKING:
    from ..community_detector import Community
    from ..graph_models import Graph
    from .bug_types import ArchitecturalBug
    from .graph_analyst import ArchitecturalInsight
    from .inspector_helpers import InspectionResult


def build_report(
    graph: Graph,
    communities: list[Community],
    insights: list[ArchitecturalInsight],
    inspection_results: list[InspectionResult],
    bugs: list[ArchitecturalBug],
    summary_text: str,
    token_summary: dict,
) -> str:
    """Assembles the full markdown report string."""
    ts = datetime.now(tz=timezone.utc).isoformat(timespec="seconds")
    sections = [
        "# Architectural Reverse Engineering Report\n",
        f"_Generated: {ts}_\n\n",
        f"## 1. Executive Summary\n\n{summary_text}\n\n",
        format_insights_section(insights),
        format_validation_section(inspection_results),
        format_bugs_section(bugs),
        format_communities_section(communities),
        format_tokens_section(token_summary),
        format_recommendations_section(bugs),
    ]
    return "\n".join(sections)


def format_insights_section(insights: list[ArchitecturalInsight]) -> str:
    """Formats the architectural insights section."""
    lines = ["## 2. Architectural Insights\n"]
    for i, insight in enumerate(insights, 1):
        lines.append(f"### {i}. {insight.title}\n")
        lines.append(f"- **Confidence:** {insight.confidence_level}\n")
        lines.append(f"- **Observation:** {insight.observation}\n")
        lines.append(f"- **Relation:** {insight.relation}\n\n")
    return "\n".join(lines)


def format_validation_section(results: list[InspectionResult]) -> str:
    """Formats the code inspection validation section."""
    lines = ["## 3. Validation Results\n\n"]
    lines.append("| Insight | Outcome | Evidence |\n")
    lines.append("|---------|---------|----------|\n")
    for result in results:
        lines.append(f"| {result.insight_title} | {result.outcome} | {result.evidence} |\n")
    return "".join(lines)


def format_bugs_section(bugs: list[ArchitecturalBug]) -> str:
    """Formats the architectural issues section, sorted by severity."""
    severity_order = [
        BugSeverity.CRITICAL,
        BugSeverity.HIGH,
        BugSeverity.MEDIUM,
        BugSeverity.LOW,
    ]
    sorted_bugs = sorted(bugs, key=lambda b: severity_order.index(b.severity))
    lines = ["\n## 4. Architectural Issues\n\n"]
    for bug in sorted_bugs:
        lines.append(f"### [{bug.severity}] {bug.bug_type}\n")
        lines.append(f"- **Description:** {bug.description}\n")
        lines.append(f"- **Recommendation:** {bug.recommendation}\n\n")
    return "".join(lines)


def format_communities_section(communities: list[Community]) -> str:
    """Formats the community overview table."""
    lines = ["\n## 5. Community Overview\n\n"]
    lines.append("| Community | Size | Cohesion |\n")
    lines.append("|-----------|------|----------|\n")
    for community in sorted(communities, key=lambda c: c.size, reverse=True):
        lines.append(
            f"| {community.dominant_label} | {community.size} | "
            f"{community.cohesion_ratio:.0%} |\n"
        )
    return "".join(lines)


def format_tokens_section(summary: dict) -> str:
    """Formats the token usage summary."""
    return (
        f"\n## 6. Token Usage\n\n"
        f"| Metric | Value |\n"
        f"|--------|-------|\n"
        f"| Prompt Tokens | {summary['total_prompt_tokens']} |\n"
        f"| Completion Tokens | {summary['total_completion_tokens']} |\n"
        f"| Total Tokens | {summary['total_tokens']} |\n"
        f"| LLM Calls | {summary['call_count']} |\n\n"
    )


def format_recommendations_section(bugs: list[ArchitecturalBug]) -> str:
    """Aggregates unique recommendations from all detected bugs."""
    unique_recs = list(dict.fromkeys(bug.recommendation for bug in bugs if bug.recommendation))
    lines = ["## 7. Recommendations\n"]
    for rec in unique_recs:
        lines.append(f"- {rec}\n")
    return "\n".join(lines)
