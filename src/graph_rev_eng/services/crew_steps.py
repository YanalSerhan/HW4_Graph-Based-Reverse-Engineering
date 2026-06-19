"""
crew_steps.py — individual autonomous step functions for AgentCrew pipeline.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from ..shared.utils import safe_execute
from .agents.report_writer import ReportWriterAgent
from .community_detector import CommunityDetector
from .github_downloader import GitHubDownloaderAgent
from .graph_loader import GraphLoader
from .index_builder import IndexBuilder

if TYPE_CHECKING:
    from pathlib import Path

    from ..graph_models import Graph
    from ..token_counter import TokenCounter
    from .crew_types import PipelineConfig

logger = logging.getLogger(__name__)


def step_clone(config: PipelineConfig, errors: list[str]) -> Path:
    """READ_ONLY clone step — autonomous."""
    from pathlib import Path

    def _do_clone() -> Path:
        agent = GitHubDownloaderAgent(cloner=config.cloner)
        return agent.run(config.github_url)

    return safe_execute(
        _do_clone,
        error_list=errors,
        default_return=Path("data/unknown"),
        error_message_prefix="Clone failed",
    )


def step_load_graph(config: PipelineConfig, errors: list[str]) -> Graph:
    """READ_ONLY graph load — autonomous."""
    from .graph_models import Graph

    def _do_load() -> Graph:
        return GraphLoader().load(config.graph_json_path)

    return safe_execute(
        _do_load,
        error_list=errors,
        default_return=Graph(),
        error_message_prefix="Graph load failed",
    )


def step_detect_communities(graph: Graph, errors: list[str]) -> Any:
    """READ_ONLY community detection — autonomous."""
    return safe_execute(
        CommunityDetector().detect,
        graph,
        error_list=errors,
        default_return=[],
        error_message_prefix="Community detection failed",
    )


def step_build_index(
    config: PipelineConfig, graph: Graph, communities: Any, errors: list[str]
) -> None:
    """REVERSIBLE index build — logged before executing."""
    logger.info("[REVERSIBLE] IndexBuilder will write to %s", config.wiki_dir)
    safe_execute(
        IndexBuilder().build,
        graph,
        communities,
        config.wiki_dir,
        error_list=errors,
        error_message_prefix="Index build failed",
    )


def step_write_report(
    config: PipelineConfig,
    graph: Graph,
    communities: Any,
    insights: Any,
    inspection_results: Any,
    bugs: Any,
    counter: TokenCounter,
    errors: list[str],
) -> Path:
    """REVERSIBLE report write — logged before executing."""
    logger.info("[REVERSIBLE] ReportWriter will write to %s", config.report_path)

    def _do_write() -> Path:
        agent = ReportWriterAgent(
            output_path=config.report_path,
            token_counter=counter,
            llm_call=config.llm_call,
        )
        return agent.run(graph, communities, insights, inspection_results, bugs)

    return safe_execute(
        _do_write,
        error_list=errors,
        default_return=config.report_path,
        error_message_prefix="Report write failed",
    )
