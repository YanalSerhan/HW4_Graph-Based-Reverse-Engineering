"""Unit tests for github_downloader.py — GitHubDownloaderAgent."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.graph_rev_eng.services.github_downloader import (
    GitHubDownloaderAgent,
    GitCloner,
)


class MockCloner:
    """Fake cloner that creates a minimal Python project directory."""

    def __init__(self, fail: bool = False) -> None:
        self._fail = fail

    def clone(self, url: str, target: Path) -> None:
        if self._fail:
            raise RuntimeError("Clone failed (mock)")
        target.mkdir(parents=True, exist_ok=True)
        (target / "main.py").write_text("def main(): pass\n")


class TestGitHubDownloaderAgent:
    def test_run_clones_to_data_dir(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        agent = GitHubDownloaderAgent(cloner=MockCloner())
        result = agent.run("https://github.com/example/my_repo")
        assert result.name == "my_repo"
        assert (result / "main.py").exists()

    def test_run_idempotent_skips_existing(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        mock_cloner = MagicMock()
        mock_cloner.clone.side_effect = lambda url, target: (
            target.mkdir(parents=True, exist_ok=True) or
            (target / "main.py").write_text("x")
        )
        agent = GitHubDownloaderAgent(cloner=mock_cloner)
        agent.run("https://github.com/example/my_repo")
        agent.run("https://github.com/example/my_repo")  # second call
        assert mock_cloner.clone.call_count == 1  # cloner only called once

    def test_run_validates_python_files(self, tmp_path: Path, monkeypatch):
        """Clone with no Python files should raise RuntimeError."""
        monkeypatch.chdir(tmp_path)

        class EmptyCloner:
            def clone(self, url: str, target: Path) -> None:
                target.mkdir(parents=True, exist_ok=True)
                (target / "README.md").write_text("no python here")

        agent = GitHubDownloaderAgent(cloner=EmptyCloner())
        with pytest.raises(RuntimeError, match="No Python files"):
            agent.run("https://github.com/example/empty_repo")

    def test_repo_name_strips_git_suffix(self):
        agent = GitHubDownloaderAgent(cloner=MockCloner())
        assert agent._repo_name("https://github.com/org/repo.git") == "repo"

    def test_repo_name_no_suffix(self):
        agent = GitHubDownloaderAgent(cloner=MockCloner())
        assert agent._repo_name("https://github.com/org/my-project") == "my-project"

    def test_clone_failure_propagates(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        agent = GitHubDownloaderAgent(cloner=MockCloner(fail=True))
        with pytest.raises(RuntimeError, match="Clone failed"):
            agent.run("https://github.com/example/fails")
