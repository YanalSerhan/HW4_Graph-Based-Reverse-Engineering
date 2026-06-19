"""
ReportWriterAgent — synthesises all agent outputs into a structured report.

Rationale: keeping report generation in its own agent means the output format
can evolve (add sections, change markdown style) without touching analysis logic.
The agent produces a single `results/final_report.md` that is the definitive
human-readable deliverable of the pipeline.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from ..community_detector import Community
from ..graph_models import Graph
from ..token_counter import TokenCounter, TokenUsage
from .base import BaseAgent, LLMStubMixin
from .bug_types import ArchitecturalBug
from .code_inspector import InspectionResult
from .graph_analyst import ArchitecturalInsight
from .report_formatter import build_report

logger = logging.getLogger(__name__)

AGENT_NAME = "ReportWriterAgent"
LLMCallable = Callable[[str], str]


class ReportWriterAgent(BaseAgent, LLMStubMixin):
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
        super().__init__(token_counter, 2000)
        self._output_path = output_path
        self._llm_call = llm_call or self._default_llm_stub

    def setup(
        self,
        graph: Graph,
        communities: list[Community],
        insights: list[ArchitecturalInsight],
        inspection_results: list[InspectionResult],
        bugs: list[ArchitecturalBug],
    ) -> tuple[
        Graph,
        list[Community],
        list[ArchitecturalInsight],
        list[InspectionResult],
        list[ArchitecturalBug],
    ]:
        """Prepares all input data for report generation."""
        return graph, communities, insights, inspection_results, bugs

    def process(
        self,
        data: tuple[
            Graph,
            list[Community],
            list[ArchitecturalInsight],
            list[InspectionResult],
            list[ArchitecturalBug],
        ],
    ) -> str:
        """Generates the executive summary via LLM and builds the full markdown report."""
        graph, communities, insights, inspection_results, bugs = data
        prompt = (
            "Write a concise executive summary based ONLY on the following findings.\n"
            "Do not invent or hallucinate any details. Use only the provided information.\n\n"
            "Insights:\n" + "\n".join(f"- {i.title}: {i.observation}" for i in insights) + "\n\n"
            "Bugs:\n" + "\n".join(f"- {b.bug_type}: {b.description}" for b in bugs)
        )
        t_in = self._counter.estimate_tokens(prompt)
        summary_text = self._llm_call(prompt)
        t_out = self._counter.estimate_tokens(summary_text)
        self._counter.record(TokenUsage(AGENT_NAME, t_in, t_out))

        return build_report(
            graph,
            communities,
            insights,
            inspection_results,
            bugs,
            summary_text,
            self._counter.summary(),
        )

    def format_output(self, report: str) -> Path:
        """Writes the generated report to disk and returns the Path."""
        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        self._output_path.write_text(report, encoding="utf-8")
        logger.info("Report written to %s (%d chars)", self._output_path, len(report))
        return self._output_path

