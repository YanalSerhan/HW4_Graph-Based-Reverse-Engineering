"""
crew_steps_agents.py — agent execution steps for the AgentCrew pipeline.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from ..shared.utils import safe_execute
from .agents.bug_detector import ArchitecturalBugDetector
from .agents.code_inspector import CodeInspectorAgent
from .agents.graph_analyst import GraphAnalystAgent

if TYPE_CHECKING:
    from pathlib import Path

    from ..graph_models import Graph
    from ..token_counter import TokenCounter
    from .crew_types import PipelineConfig

logger = logging.getLogger(__name__)


def step_analyse(
    config: PipelineConfig,
    graph: Graph,
    communities: Any,
    repo_path: Path,
    counter: TokenCounter,
    budget: int,
    errors: list[str],
) -> Any:
    """READ_ONLY graph analysis — autonomous."""

    def _do_analyse():
        agent = GraphAnalystAgent(
            counter,
            llm_call=config.llm_call,
            token_budget=budget,
        )
        return agent.run(
            graph,
            communities,
            graph_html_path=config.graph_html_path,
            graph_report_path=config.graph_report_path,
        )

    return safe_execute(
        _do_analyse,
        error_list=errors,
        default_return=[],
        error_message_prefix="Graph analysis failed",
    )


def step_inspect(
    config: PipelineConfig,
    graph: Graph,
    insights: Any,
    repo_path: Path,
    counter: TokenCounter,
    budget: int,
    errors: list[str],
) -> Any:
    """READ_ONLY source inspection — autonomous."""

    def _do_inspect():
        agent = CodeInspectorAgent(
            repo_path=repo_path,
            token_counter=counter,
            llm_call=config.llm_call,
            token_budget=budget,
        )
        return agent.run(graph, insights)

    return safe_execute(
        _do_inspect,
        error_list=errors,
        default_return=[],
        error_message_prefix="Code inspection failed",
    )


def step_detect_bugs(
    config: PipelineConfig,
    graph: Graph,
    communities: Any,
    counter: TokenCounter,
    budget: int,
    errors: list[str],
) -> Any:
    """READ_ONLY bug detection — autonomous."""

    def _do_detect():
        agent = ArchitecturalBugDetector(
            counter,
            llm_call=config.llm_call,
            token_budget=budget,
        )
        return agent.run(graph, communities)

    return safe_execute(
        _do_detect,
        error_list=errors,
        default_return=[],
        error_message_prefix="Bug detection failed",
    )
