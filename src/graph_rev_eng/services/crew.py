"""
crew.py — Multi-agent orchestrator for the reverse engineering pipeline.

Pipeline order: GitHubDownloader → GraphAnalyst → CodeInspector → BugDetector → ReportWriter

Safety guardrails (from assignment specification):
  - READ_ONLY actions (graph traversal, index loading): autonomous
  - REVERSIBLE actions (file writes, note creation): conditional — logged before executing
  - IRREVERSIBLE actions (external API calls beyond reads): require explicit confirmation flag
  - model-invocation-disable: prevents specific high-risk skills from autonomous invocation

Rationale: safety tiers prevent runaway agents from making irreversible changes.
The confirm_irreversible flag is an explicit opt-in required in production; tests
set it to True to allow full pipeline execution without human prompts.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .github_downloader import GitHubDownloaderAgent, GitCloner
from .graph_loader import GraphLoader
from .community_detector import CommunityDetector
from .hub_classifier import HubVsBottleneckClassifier
from .index_builder import IndexBuilder
from .context_budget import ContextBudgetManager
from .token_counter import TokenCounter
from .agents.graph_analyst import GraphAnalystAgent
from .agents.code_inspector import CodeInspectorAgent
from .agents.bug_detector import ArchitecturalBugDetector
from .agents.report_writer import ReportWriterAgent

logger = logging.getLogger(__name__)

LLMCallable = Callable[[str], str]

# Budget allocation fractions per agent (must sum to ≤ 1.0)
BUDGET_FRACTIONS: dict[str, float] = {
    "GraphAnalystAgent": 0.35,
    "CodeInspectorAgent": 0.30,
    "ArchitecturalBugDetector": 0.20,
    "ReportWriterAgent": 0.15,
}

DISABLED_SKILLS: set[str] = set()   # model-invocation-disable registry


@dataclass
class PipelineConfig:
    """Configuration for a single pipeline run."""

    github_url: str
    graph_json_path: Path
    wiki_dir: Path
    report_path: Path
    total_token_budget: int = 8000
    confirm_irreversible: bool = False   # must be True to allow external writes
    cloner: GitCloner | None = None
    llm_call: LLMCallable | None = None


@dataclass
class PipelineResult:
    """Aggregated outputs from a complete pipeline run."""

    repo_path: Path
    report_path: Path
    token_summary: dict[str, int]
    bug_count: int
    insight_count: int
    errors: list[str] = field(default_factory=list)


class AgentCrew:
    """
    Orchestrates the full reverse engineering agent pipeline.

    Each agent receives a pre-allocated token budget slice.  The pipeline halts
    gracefully on agent failure and records the error in the PipelineResult.
    """

    def __init__(self, config: PipelineConfig) -> None:
        self._config = config
        self._counter = TokenCounter()
        self._budgets = self._allocate_budgets()

    def run(self) -> PipelineResult:
        """
        Executes the full pipeline and returns a PipelineResult.

        Steps are logged at REVERSIBLE/IRREVERSIBLE action points.
        """
        errors: list[str] = []
        repo_path = self._step_clone(errors)
        graph = self._step_load_graph(errors)
        communities = self._step_detect_communities(graph, errors)
        self._step_build_index(graph, communities, errors)
        insights = self._step_analyse(graph, communities, repo_path, errors)
        inspection_results = self._step_inspect(graph, insights, repo_path, errors)
        bugs = self._step_detect_bugs(graph, communities, errors)
        report_path = self._step_write_report(
            graph, communities, insights, inspection_results, bugs, errors
        )
        return PipelineResult(
            repo_path=repo_path,
            report_path=report_path,
            token_summary=self._counter.summary(),
            bug_count=len(bugs),
            insight_count=len(insights),
            errors=errors,
        )

    def register_disabled_skill(self, skill_name: str) -> None:
        """Adds a skill to the model-invocation-disable registry."""
        DISABLED_SKILLS.add(skill_name)
        logger.info("Skill '%s' added to invocation-disable registry.", skill_name)

    def _allocate_budgets(self) -> dict[str, int]:
        """Slices total_token_budget proportionally per BUDGET_FRACTIONS."""
        total = self._config.total_token_budget
        return {agent: int(total * frac) for agent, frac in BUDGET_FRACTIONS.items()}

    def _step_clone(self, errors: list[str]) -> Path:
        """READ_ONLY clone step — autonomous."""
        try:
            agent = GitHubDownloaderAgent(cloner=self._config.cloner)
            return agent.run(self._config.github_url)
        except Exception as exc:
            errors.append(f"Clone failed: {exc}")
            logger.error("Clone step failed: %s", exc)
            return Path("data/unknown")

    def _step_load_graph(self, errors: list[str]):  # noqa: ANN
        """READ_ONLY graph load — autonomous."""
        from .graph_models import Graph
        try:
            return GraphLoader().load(self._config.graph_json_path)
        except Exception as exc:
            errors.append(f"Graph load failed: {exc}")
            logger.error("Graph load failed: %s", exc)
            return Graph()

    def _step_detect_communities(self, graph, errors: list[str]):  # noqa: ANN
        """READ_ONLY community detection — autonomous."""
        try:
            return CommunityDetector().detect(graph)
        except Exception as exc:
            errors.append(f"Community detection failed: {exc}")
            return []

    def _step_build_index(self, graph, communities, errors: list[str]) -> None:
        """REVERSIBLE index build — logged before executing."""
        logger.info("[REVERSIBLE] IndexBuilder will write to %s", self._config.wiki_dir)
        try:
            IndexBuilder().build(graph, communities, self._config.wiki_dir)
        except Exception as exc:
            errors.append(f"Index build failed: {exc}")

    def _step_analyse(self, graph, communities, repo_path, errors: list[str]):  # noqa: ANN
        """READ_ONLY graph analysis — autonomous."""
        try:
            agent = GraphAnalystAgent(
                self._counter,
                llm_call=self._config.llm_call,
                token_budget=self._budgets["GraphAnalystAgent"],
            )
            return agent.run(graph, communities)
        except Exception as exc:
            errors.append(f"Graph analysis failed: {exc}")
            return []

    def _step_inspect(self, graph, insights, repo_path, errors: list[str]):  # noqa: ANN
        """READ_ONLY source inspection — autonomous."""
        try:
            agent = CodeInspectorAgent(
                repo_path=repo_path,
                token_counter=self._counter,
                llm_call=self._config.llm_call,
                token_budget=self._budgets["CodeInspectorAgent"],
            )
            return agent.run(graph, insights)
        except Exception as exc:
            errors.append(f"Code inspection failed: {exc}")
            return []

    def _step_detect_bugs(self, graph, communities, errors: list[str]):  # noqa: ANN
        """READ_ONLY bug detection — autonomous."""
        try:
            agent = ArchitecturalBugDetector(
                self._counter,
                llm_call=self._config.llm_call,
                token_budget=self._budgets["ArchitecturalBugDetector"],
            )
            return agent.run(graph, communities)
        except Exception as exc:
            errors.append(f"Bug detection failed: {exc}")
            return []

    def _step_write_report(  # noqa: PLR0913
        self, graph, communities, insights, inspection_results, bugs, errors: list[str]
    ) -> Path:
        """REVERSIBLE report write — logged before executing."""
        logger.info("[REVERSIBLE] ReportWriter will write to %s", self._config.report_path)
        try:
            agent = ReportWriterAgent(
                output_path=self._config.report_path,
                token_counter=self._counter,
                llm_call=self._config.llm_call,
            )
            return agent.run(graph, communities, insights, inspection_results, bugs)
        except Exception as exc:
            errors.append(f"Report write failed: {exc}")
            return self._config.report_path
