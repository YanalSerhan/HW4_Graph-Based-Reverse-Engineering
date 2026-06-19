"""
crew.py — orchestrates the multi-agent execution pipeline.

This module provides the central AgentCrew which controls the execution flow
of all specialized agents. It handles dependency injection (budgets, token
counters), coordinates sequential agent execution, and maintains a registry
of disabled skills.
"""

from __future__ import annotations

import logging

from .crew_steps import (
    step_build_index,
    step_clone,
    step_detect_communities,
    step_load_graph,
    step_write_report,
)
from .crew_steps_agents import (
    step_detect_bugs,
)
from .crew_types import PipelineConfig, PipelineResult
from .improvement_loop import run_improvement_loop
from .token_counter import TokenCounter

logger = logging.getLogger(__name__)

BUDGET_FRACTIONS = {
    "GraphAnalystAgent": 0.5,
    "CodeInspectorAgent": 0.25,
    "ArchitecturalBugDetector": 0.25,
}

DISABLED_SKILLS: set[str] = set()


class AgentCrew:
    """Orchestrator for the multi-agent reverse-engineering pipeline."""

    def __init__(self, config: PipelineConfig) -> None:
        self._config = config
        self._counter = TokenCounter()
        self._budgets = self._allocate_budgets()

    def run(self) -> PipelineResult:
        """Executes the full multi-agent pipeline from clone to report."""
        errors: list[str] = []

        repo_path = step_clone(self._config, errors)
        graph = step_load_graph(self._config, errors)
        communities = step_detect_communities(graph, errors)

        step_build_index(self._config, graph, communities, errors)

        from .crew_orchestrator import run_crew_orchestration
        insights, inspection_results, bugs = run_crew_orchestration(
            self._config,
            graph,
            communities,
            repo_path,
            self._counter,
            self._budgets,
            errors,
        )

        def _load_graph_cb(errs):
            return step_load_graph(self._config, errs)

        def _detect_comm_cb(g, errs):
            return step_detect_communities(g, errs)

        def _detect_bugs_cb(g, c, errs):
            return step_detect_bugs(
                self._config, g, c, self._counter, self._budgets["ArchitecturalBugDetector"], errs
            )

        graph, communities, bugs = run_improvement_loop(
            graph,
            communities,
            bugs,
            repo_path,
            errors,
            load_graph_cb=_load_graph_cb,
            detect_communities_cb=_detect_comm_cb,
            detect_bugs_cb=_detect_bugs_cb,
        )

        report_path = step_write_report(
            self._config,
            graph,
            communities,
            insights,
            inspection_results,
            bugs,
            self._counter,
            errors,
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
