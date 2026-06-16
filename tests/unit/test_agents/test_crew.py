"""Unit tests for services/crew.py — AgentCrew, PipelineConfig, PipelineResult."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.graph_rev_eng.services.crew import AgentCrew, PipelineConfig, PipelineResult


class MockCloner:
    """Creates a minimal Python repo so validation passes."""
    def clone(self, url: str, target: Path) -> None:
        target.mkdir(parents=True, exist_ok=True)
        (target / "main.py").write_text("def run(): pass\n")


def _make_config(tmp_path: Path, has_graph: bool = True) -> PipelineConfig:
    """Builds a PipelineConfig pointing at temp directories."""
    results = tmp_path / "results"
    results.mkdir()
    graph_path = results / "graph.json"

    if has_graph:
        graph_data = {
            "nodes": [
                {"id": "n1", "label": "module_a", "type": "module", "file_path": "src/a.py"},
                {"id": "n2", "label": "module_b", "type": "module", "file_path": "src/b.py"},
            ],
            "edges": [
                {"source": "n1", "target": "n2", "type": "EXTRACTED", "confidence": 1.0}
            ],
            "hyperedges": [],
        }
        graph_path.write_text(json.dumps(graph_data), encoding="utf-8")

    return PipelineConfig(
        github_url="https://github.com/example/repo",
        graph_json_path=graph_path,
        wiki_dir=tmp_path / "wiki",
        report_path=results / "final_report.md",
        total_token_budget=4000,
        cloner=MockCloner(),
        llm_call=lambda p: "[MOCK]",
    )


class TestAgentCrew:
    def test_run_returns_pipeline_result(self, tmp_path: Path):
        config = _make_config(tmp_path)
        result = AgentCrew(config).run()
        assert isinstance(result, PipelineResult)

    def test_run_produces_report_file(self, tmp_path: Path):
        config = _make_config(tmp_path)
        result = AgentCrew(config).run()
        assert result.report_path.exists()

    def test_run_includes_token_summary(self, tmp_path: Path):
        config = _make_config(tmp_path)
        result = AgentCrew(config).run()
        assert "total_tokens" in result.token_summary

    def test_run_missing_graph_records_error(self, tmp_path: Path):
        config = _make_config(tmp_path, has_graph=False)
        result = AgentCrew(config).run()
        assert len(result.errors) > 0

    def test_budget_fractions_sum_to_one_or_less(self):
        from src.graph_rev_eng.services.crew import BUDGET_FRACTIONS
        assert sum(BUDGET_FRACTIONS.values()) <= 1.0

    def test_register_disabled_skill(self, tmp_path: Path):
        config = _make_config(tmp_path)
        crew = AgentCrew(config)
        crew.register_disabled_skill("dangerous_skill")
        from src.graph_rev_eng.services.crew import DISABLED_SKILLS
        assert "dangerous_skill" in DISABLED_SKILLS
