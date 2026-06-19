"""
ReverseEngineeringSDK — single entry point for all business logic.

Every external caller (CLI, tests, notebooks) must go through this class.
No business logic exists outside services/ accessed via this SDK.
"""

from __future__ import annotations

from pathlib import Path

from ..services.community_detector import CommunityDetector
from ..services.crew import AgentCrew, PipelineConfig, PipelineResult
from ..services.github_downloader import GitCloner
from ..services.graph_loader import GraphLoader
from ..services.graph_models import Graph
from ..services.index_builder import IndexBuilder
from ..services.skill_router import RoutingResult, SkillRouter
from ..services.token_counter import TokenCounter
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

    def run_grphify(self, repo_path: str) -> tuple[Path, Path, Path]:
        """
        Runs the Grphify CLI on repo_path and returns paths to
        (graph.json, graph.html, GRAPH_REPORT.md).

        In production, shells out to `grphify scan <repo_path>`.
        """
        import subprocess

        output_path = RESULTS_DIR / "graph.json"
        html_path = RESULTS_DIR / "graph.html"
        report_path = RESULTS_DIR / "GRAPH_REPORT.md"
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
            # Grphify not installed or failed — fall back to internal AST parser
            import json
            import logging
            from dataclasses import asdict

            from ..services.ast_parser import ASTGraphBuilder

            logging.getLogger(__name__).warning(
                "Grphify unavailable (%s). Falling back to internal AST parser.", exc
            )

            graph = ASTGraphBuilder().build(Path(repo_path))

            nodes_json = []
            for v in graph.nodes.values():
                d = asdict(v)
                d["id"] = d.pop("node_id")
                d["type"] = d.pop("node_type")
                nodes_json.append(d)

            edges_json = []
            for e in graph.edges:
                d = asdict(e)
                d["source"] = d.pop("source_id")
                d["target"] = d.pop("target_id")
                d["type"] = d.pop("edge_type")
                edges_json.append(d)

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump({
                    "nodes": nodes_json,
                    "edges": edges_json,
                    "hyperedges": [],
                    "metadata": {}
                }, f, indent=2)

        # Ensure dummy outputs if they don't exist, to satisfy agents in mock environments
        if not html_path.exists():
            html_path.write_text(
                "<html><body>Mock Graph HTML Metadata</body></html>", encoding="utf-8"
            )
        if not report_path.exists():
            report_path.write_text(
                "# Mock GRAPH_REPORT\nNo actual Grphify output available.", encoding="utf-8"
            )

        return output_path, html_path, report_path

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
