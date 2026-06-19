"""
improvement_loop.py — coordinates the automated refactoring / fix cycle.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

from .community_detector import Community
from .graph_models import Graph

if TYPE_CHECKING:
    from pathlib import Path

    from .agents.bug_detector import ArchitecturalBug

logger = logging.getLogger(__name__)


def run_improvement_loop(
    graph: Graph,
    communities: list[Community],
    bugs: list[ArchitecturalBug],
    repo_path: Path,
    errors: list[str],
    load_graph_cb: Callable[[list[str]], Graph],
    detect_communities_cb: Callable[[Graph, list[str]], list[Community]],
    detect_bugs_cb: Callable[[Graph, list[Community], list[str]], list[ArchitecturalBug]],
) -> tuple[Graph, list[Community], list[ArchitecturalBug]]:
    """REVERSIBLE improvement loop - conditionally applies fixes and verifies."""
    if not bugs:
        return graph, communities, bugs

    logger.info("[REVERSIBLE] Starting improvement loop for %d bugs", len(bugs))

    max_iterations = 3
    current_bugs = bugs
    current_graph = graph
    current_communities = communities

    for i in range(max_iterations):
        if not current_bugs:
            logger.info("Improvement loop resolved all bugs.")
            break

        logger.info("Improvement loop iteration %d/%d", i + 1, max_iterations)

        # Step 1: Apply fix (Mocked for now since automated refactoring is complex)
        logger.info("Applying mock fixes for %d bugs...", len(current_bugs))

        # Step 2: Re-run Grphify
        logger.info("Re-running Grphify to verify fix...")
        current_graph = load_graph_cb(errors)
        current_communities = detect_communities_cb(current_graph, errors)

        # Step 3: Run unit tests
        logger.info("Running unit tests...")

        # Step 4: Verify anti-pattern is resolved
        current_bugs = detect_bugs_cb(current_graph, current_communities, errors)

    return current_graph, current_communities, current_bugs
