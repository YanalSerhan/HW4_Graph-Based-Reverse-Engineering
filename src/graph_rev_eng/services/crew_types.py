"""
crew_types.py — configuration and result types for the AgentCrew pipeline.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .github_downloader import GitCloner


@dataclass
class PipelineConfig:
    github_url: str
    graph_json_path: Path
    wiki_dir: Path
    report_path: Path
    graph_html_path: Path = field(default_factory=lambda: Path("artifacts/graph.html"))
    graph_report_path: Path = field(default_factory=lambda: Path("artifacts/graph_report.md"))
    cloner: type[GitCloner] | None = None
    llm_call: Callable[[str], str] | None = None
    total_token_budget: int = 10000


@dataclass
class PipelineResult:
    repo_path: Path
    report_path: Path
    token_summary: str
    bug_count: int
    insight_count: int
    errors: list[str] = field(default_factory=list)
