"""
GitHubDownloaderAgent — clones a GitHub repository into the data/ directory.

Rationale: isolating cloning logic into its own agent makes the operation
mockable in tests (inject a fake git.Repo factory) and keeps main orchestration
free of subprocess boilerplate. BugsInPy-specific setup is documented and
wrapped in a separate method so it can be skipped for other repos.
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Protocol

logger = logging.getLogger(__name__)

DATA_DIR = Path("data")


class GitCloner(Protocol):
    """
    Protocol for git clone operations — enables dependency injection in tests.

    Any object with a matching clone() signature satisfies this interface.
    """

    def clone(self, url: str, target: Path) -> None:
        """Clone the repository at url into target directory."""
        ...


class SubprocessGitCloner:
    """Production implementation using the system git binary."""

    def clone(self, url: str, target: Path) -> None:
        """Clones url into target via subprocess git clone."""
        result = subprocess.run(
            ["git", "clone", "--depth=1", url, str(target)],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            raise RuntimeError(f"git clone failed for {url}:\n{result.stderr}")


class GitHubDownloaderAgent:
    """
    Downloads and validates a GitHub repository for analysis.

    The agent always clones into a subdirectory of DATA_DIR named after the
    repository (last path segment of the URL). If the target already exists
    the clone is skipped and the existing path is returned — idempotent.
    """

    def __init__(self, cloner: GitCloner | None = None) -> None:
        self._cloner: GitCloner = cloner or SubprocessGitCloner()

    def run(self, github_url: str) -> Path:
        """
        Clones the repository and returns the local path.

        Raises RuntimeError if the clone fails or target Python files are absent.
        """
        repo_name = self._repo_name(github_url)
        target = DATA_DIR / repo_name

        if target.exists():
            logger.info("Repository already exists at %s — skipping clone.", target)
        else:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            logger.info("Cloning %s → %s", github_url, target)
            self._cloner.clone(github_url, target)

        self._validate(target)
        return target

    def setup_bugsinpy(self, repo_path: Path) -> None:
        """
        Sets up the BugsInPy virtual environment per its README instructions.

        BugsInPy requires a specific venv layout; this method encapsulates that
        friction so the main workflow remains clean.  Any errors are logged and
        re-raised so the orchestrator can halt gracefully.
        """
        setup_script = repo_path / "setup.sh"
        if not setup_script.exists():
            logger.warning("BugsInPy setup.sh not found at %s — skipping.", setup_script)
            return
        logger.info("Running BugsInPy environment setup at %s", repo_path)
        result = subprocess.run(
            ["bash", str(setup_script)],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            timeout=600,
        )
        if result.returncode != 0:
            raise RuntimeError(f"BugsInPy setup failed:\n{result.stderr}")
        logger.info("BugsInPy environment ready.")

    def _repo_name(self, url: str) -> str:
        """Extracts the repository name from the GitHub URL."""
        name = url.rstrip("/").split("/")[-1]
        return name.removesuffix(".git")

    def _validate(self, repo_path: Path) -> None:
        """
        Confirms Python files are accessible in the cloned repository.

        Raises RuntimeError if no .py files are found — this prevents
        downstream Grphify from silently producing an empty graph.
        """
        py_files = list(repo_path.glob("**/*.py"))
        if not py_files:
            raise RuntimeError(
                f"No Python files found in cloned repo at {repo_path}. "
                "Confirm the URL points to a Python project."
            )
        logger.info("Clone validated: %d Python files found.", len(py_files))
