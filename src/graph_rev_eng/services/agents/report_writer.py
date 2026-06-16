"""
ReportWriterAgent — synthesises all agent outputs into a structured report.

Rationale: keeping report generation in its own agent means the output format
can evolve (add sections, change markdown style) without touching analysis logic.
The agent produces a single `results/final_report.md` that is the definitive
human-readable deliverable of the pipeline.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from ..graph_models import Graph
from ..community_detector import Community
from ..token_counter import TokenCounter, TokenUsage
from .graph_analyst import ArchitecturalInsight
from .code_inspector import InspectionResult, ValidationOutcome
from .bug_detector import ArchitecturalBug, BugSeverity

logger = logging.getLogger(__name__)

AGENT_NAME = "ReportWriterAgent"
LLMCallable = Callable[[str], str]


class ReportWriterAgent:
    """
    Synthesises insights, inspection results, and bug findings into a report.

    The report is structured as:
      1. Executive Summary
      2. Architectural Insights (from GraphAnalystAgent)
      3. Validation Results (from CodeInspectorAgent)
      4. Architectural Issues (from BugDetector)
      5. Token Usage Summary
      6. Recommendations
    """

    def __init__(
        self,
        output_path: Path,
        token_counter: TokenCounter,
        llm_call: LLMCallable | None = None,
    ) -> None:
        self._output_path = output_path
        self._counter = token_counter
        self._llm_call = llm_call or self._default_llm_stub

    def run(
        self,
        graph: Graph,
        communities: list[Community],
        insights: list[ArchitecturalInsight],
        inspection_results: list[InspectionResult],
        bugs: list[ArchitecturalBug],
    ) -> Path:
        """
        Generates the final report and writes it to output_path.

        Returns the path to the written report.
        """
        prompt = f"Summarise findings: {len(insights)} insights, {len(bugs)} bugs."
        t_in = self._counter.estimate_tokens(prompt)
        summary_text = self._llm_call(prompt)
        t_out = self._counter.estimate_tokens(summary_text)
        self._counter.record(TokenUsage(AGENT_NAME, t_in, t_out))

        report = self._build_report(graph, communities, insights, inspection_results, bugs, summary_text)
        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        self._output_path.write_text(report, encoding="utf-8")
        logger.info("Report written to %s (%d chars)", self._output_path, len(report))
        return self._output_path

    def _build_report(
        self,
        graph: Graph,
        communities: list[Community],
        insights: list[ArchitecturalInsight],
        inspection_results: list[InspectionResult],
        bugs: list[ArchitecturalBug],
        summary_text: str,
    ) -> str:
        """Assembles the full markdown report string."""
        ts = datetime.now(tz=timezone.utc).isoformat(timespec="seconds")
        sections = [
            f"# Architectural Reverse Engineering Report\n",
            f"_Generated: {ts}_\n\n",
            f"## 1. Executive Summary\n\n{summary_text}\n\n",
            self._insights_section(insights),
            self._validation_section(inspection_results),
            self._bugs_section(bugs),
            self._communities_section(communities),
            self._tokens_section(),
            self._recommendations_section(bugs),
        ]
        return "\n".join(sections)

    def _insights_section(self, insights: list[ArchitecturalInsight]) -> str:
        """Formats the architectural insights section."""
        lines = ["## 2. Architectural Insights\n"]
        for i, insight in enumerate(insights, 1):
            lines.append(f"### {i}. {insight.title}\n")
            lines.append(f"- **Confidence:** {insight.confidence_level}\n")
            lines.append(f"- **Observation:** {insight.observation}\n")
            lines.append(f"- **Relation:** {insight.relation}\n\n")
        return "\n".join(lines)

    def _validation_section(self, results: list[InspectionResult]) -> str:
        """Formats the code inspection validation section."""
        lines = ["## 3. Validation Results\n\n"]
        lines.append("| Insight | Outcome | Evidence |\n")
        lines.append("|---------|---------|----------|\n")
        for result in results:
            lines.append(
                f"| {result.insight_title} | {result.outcome} | {result.evidence} |\n"
            )
        return "".join(lines)

    def _bugs_section(self, bugs: list[ArchitecturalBug]) -> str:
        """Formats the architectural issues section, sorted by severity."""
        severity_order = [BugSeverity.CRITICAL, BugSeverity.HIGH, BugSeverity.MEDIUM, BugSeverity.LOW]
        sorted_bugs = sorted(bugs, key=lambda b: severity_order.index(b.severity))
        lines = ["\n## 4. Architectural Issues\n\n"]
        for bug in sorted_bugs:
            lines.append(f"### [{bug.severity}] {bug.bug_type}\n")
            lines.append(f"- **Description:** {bug.description}\n")
            lines.append(f"- **Recommendation:** {bug.recommendation}\n\n")
        return "".join(lines)

    def _communities_section(self, communities: list[Community]) -> str:
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

    def _tokens_section(self) -> str:
        """Formats the token usage summary."""
        summary = self._counter.summary()
        return (
            f"\n## 6. Token Usage\n\n"
            f"| Metric | Value |\n"
            f"|--------|-------|\n"
            f"| Prompt Tokens | {summary['total_prompt_tokens']} |\n"
            f"| Completion Tokens | {summary['total_completion_tokens']} |\n"
            f"| Total Tokens | {summary['total_tokens']} |\n"
            f"| LLM Calls | {summary['call_count']} |\n\n"
        )

    def _recommendations_section(self, bugs: list[ArchitecturalBug]) -> str:
        """Aggregates unique recommendations from all detected bugs."""
        unique_recs = list(dict.fromkeys(bug.recommendation for bug in bugs if bug.recommendation))
        lines = ["## 7. Recommendations\n"]
        for rec in unique_recs:
            lines.append(f"- {rec}\n")
        return "\n".join(lines)

    def _default_llm_stub(self, prompt: str) -> str:
        """Deterministic stub for test environments."""
        return "[STUB] Executive summary pending LLM configuration."
