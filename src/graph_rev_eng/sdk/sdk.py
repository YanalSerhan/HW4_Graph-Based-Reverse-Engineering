"""
ReverseEngineeringSDK — single entry point for all business logic.

Every external caller (CLI, tests, notebooks) must go through this class.
No business logic exists outside services/ accessed via this SDK.
"""

from __future__ import annotations

from pathlib import Path

from ..services.community_detector import CommunityDetector
from ..services.crew import AgentCrew
from ..services.crew_types import PipelineConfig, PipelineResult
from ..services.github_downloader import GitCloner
from ..services.graph_loader import GraphLoader
from ..services.graph_models import Graph
from ..services.index_builder import IndexBuilder
from ..services.skill_router import RoutingResult, SkillRouter
from ..services.token_counter import TokenCounter
from ..shared.config import ConfigManager
from .grphify_runner import run_grphify_cli

RESULTS_DIR = Path("results")
WIKI_DIR = RESULTS_DIR / "wiki"


class ReverseEngineeringSDK:
    """
    Single entry point for all reverse engineering business logic.

    Wires together the service layer so callers never import service classes
    directly. Configuration is loaded from ConfigManager on init.
    """

    def __init__(self) -> None:
        self._config = ConfigManager.get_instance()
        self._token_counter = TokenCounter()

    def run_grphify(self, repo_path: str) -> tuple[Path, Path, Path]:
        """
        Runs the Grphify CLI on repo_path and returns paths to
        (graph.json, graph.html, GRAPH_REPORT.md).

        In production, shells out to `grphify scan <repo_path>`.
        """
        return run_grphify_cli(repo_path, RESULTS_DIR)

    def load_graph(self, graph_path: Path) -> Graph:
        """Loads and validates a Graph from the given graph.json path."""
        return GraphLoader().load(graph_path)

    def build_index(self, graph: Graph) -> Path:
        """
        Builds the LLM Wiki index from a Graph.

        Returns the wiki output directory path.
        """
        communities = CommunityDetector().detect(graph)
        IndexBuilder().build(graph, communities, WIKI_DIR)
        return WIKI_DIR

    def route_skill(self, query: str, skills_dir: Path | None = None) -> RoutingResult:
        """Routes a natural language query to the most relevant SKILL.md."""
        return SkillRouter(skills_dir=skills_dir).route(query)

    def run_agents(
        self,
        task: str,
        github_url: str = "",
        graph_path: Path | None = None,
        graph_html_path: Path | None = None,
        graph_report_path: Path | None = None,
        report_path: Path | None = None,
        cloner: GitCloner | None = None,
        llm_call=None,
    ) -> PipelineResult:
        """
        Orchestrates the full multi-agent pipeline for the given task.

        Returns a PipelineResult with report path and token usage summary.
        """
        if llm_call is None:
            from ..services.llm import OpenAILLM
            from ..shared.gatekeeper import ApiGatekeeper, RateLimitConfig

            rate_limits = self._config.get_rate_limits()
            rl_config = RateLimitConfig.from_dict(rate_limits)
            gatekeeper = ApiGatekeeper(rl_config)

            api_key = self._config.get_api_key("LLM_API_KEY")
            llm_call = OpenAILLM(gatekeeper, api_key)

        config = PipelineConfig(
            github_url=github_url,
            graph_json_path=graph_path or (RESULTS_DIR / "graph.json"),
            graph_html_path=graph_html_path or (RESULTS_DIR / "graph.html"),
            graph_report_path=graph_report_path or (RESULTS_DIR / "GRAPH_REPORT.md"),
            wiki_dir=WIKI_DIR,
            report_path=report_path or (RESULTS_DIR / "final_report.md"),
            total_token_budget=self._config.get_rate_limits().get("default_token_budget", 8000),
            cloner=cloner,
            llm_call=llm_call,
        )
        return AgentCrew(config).run()
