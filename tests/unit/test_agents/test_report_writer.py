"""Unit tests for agents/report_writer.py — ReportWriterAgent."""

from __future__ import annotations

from pathlib import Path

from graph_rev_eng.constants import EDGE_TYPE_INFERRED
from graph_rev_eng.services.agents.bug_detector import ArchitecturalBug, BugSeverity
from graph_rev_eng.services.agents.code_inspector import InspectionResult, ValidationOutcome
from graph_rev_eng.services.agents.graph_analyst import ArchitecturalInsight
from graph_rev_eng.services.agents.report_writer import ReportWriterAgent


class TestReportWriterAgent:
    def test_run_writes_report(self, tmp_path: Path, simple_graph, token_counter, mock_llm_call):
        report_path = tmp_path / "final_report.md"
        agent = ReportWriterAgent(
            output_path=report_path,
            token_counter=token_counter,
            llm_call=mock_llm_call,
        )

        insights = [
            ArchitecturalInsight(
                title="Insight",
                observation="obs",
                relation="rel",
                confidence_level=EDGE_TYPE_INFERRED,
                context="ctx",
                source_node_ids=["n1"],
            )
        ]
        inspections = [
            InspectionResult(
                insight_title="Insight",
                outcome=ValidationOutcome.CONFIRMED,
                evidence="Found",
            )
        ]
        bugs = [
            ArchitecturalBug(
                bug_type="SPOF",
                severity=BugSeverity.HIGH,
                description="desc",
                recommendation="Fix it",
                affected_node_ids=["n1"],
            )
        ]

        result_path = agent.run(simple_graph, [], insights, inspections, bugs)
        assert result_path == report_path
        assert report_path.exists()
        content = report_path.read_text(encoding="utf-8")
        assert "Insight" in content
        assert "CONFIRMED" in content
        assert "SPOF" in content
        assert "Fix it" in content

    def test_empty_inputs(self, tmp_path: Path, simple_graph, token_counter, mock_llm_call):
        report_path = tmp_path / "empty_report.md"
        agent = ReportWriterAgent(
            output_path=report_path,
            token_counter=token_counter,
            llm_call=mock_llm_call,
        )
        agent.run(simple_graph, [], [], [], [])
        assert report_path.exists()
        assert "Executive Summary" in report_path.read_text(encoding="utf-8")
