"""
ReverseEngineeringSDK — single entry point for all business logic.

Every external caller (CLI, tests, notebooks) must go through this class.
No business logic exists outside services/ accessed via this SDK.
"""

from __future__ import annotations

from pathlib import Path

from ..services.github_downloader import GitHubDownloaderAgent, GitCloner
from ..services.graph_loader import GraphLoader
from ..services.graph_models import Graph
from ..services.community_detector import CommunityDetector
from ..services.index_builder import IndexBuilder
from ..services.skill_router import SkillRouter, RoutingResult
from ..services.token_counter import TokenCounter
from ..services.crew import AgentCrew, PipelineConfig, PipelineResult
from ..shared.config import ConfigManager

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

    def run_grphify(self, repo_path: str) -> Path:
        """
        Runs the Grphify CLI on repo_path and returns the path to graph.json.

        In production, shells out to `grphify scan <repo_path>`.
        In test/mock mode, returns the pre-existing path if it exists.
        """
        import subprocess

        output_path = RESULTS_DIR / "graph.json"
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(
                ["grphify", "scan", repo_path, "--output", str(output_path)],
                check=True,
                capture_output=True,
                text=True,
                timeout=600,
            )
        except (FileNotFoundError, subprocess.CalledProcessError) as exc:
            # Grphify not installed or failed — fall back to existing path
            import logging
            logging.getLogger(__name__).warning(
                "Grphify unavailable (%s). Using existing graph at %s.", exc, output_path
            )
        return output_path

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
        report_path: Path | None = None,
        cloner: GitCloner | None = None,
        llm_call=None,
    ) -> PipelineResult:
        """
        Orchestrates the full multi-agent pipeline for the given task.

        Returns a PipelineResult with report path and token usage summary.
        """
        config = PipelineConfig(
            github_url=github_url,
            graph_json_path=graph_path or (RESULTS_DIR / "graph.json"),
            wiki_dir=WIKI_DIR,
            report_path=report_path or (RESULTS_DIR / "final_report.md"),
            total_token_budget=self._config.get_rate_limits().get(
                "default_token_budget", 8000
            ),
            cloner=cloner,
            llm_call=llm_call,
        )
        return AgentCrew(config).run()
