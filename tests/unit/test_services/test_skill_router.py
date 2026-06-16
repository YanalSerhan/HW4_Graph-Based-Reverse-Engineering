"""Unit tests for skill_router.py — SkillRouter, Skill, RoutingResult."""

from __future__ import annotations

from pathlib import Path

import pytest

from graph_rev_eng.services.skill_router import SkillRouter


SKILL_CONTENT = """\
---
name: graph_analysis
triggers:
  - analyse architecture
  - architectural analysis
  - graph analysis
boundaries: requires graph.json
routing_subgraph: community_analysis
---

# SKILL: Graph Analysis

Step 1 — Observe the graph.
"""

SKILL_CONTENT_2 = """\
---
name: bug_detection
triggers:
  - detect bugs
  - find anti-patterns
  - spof detection
boundaries: read-only
routing_subgraph: bug_detection_map
---

# SKILL: Bug Detection

Step 1 — Run detection passes.
"""


@pytest.fixture()
def skills_dir(tmp_path: Path) -> Path:
    """Creates a temp skills directory with 2 skill files."""
    skills = tmp_path / "skills"
    skills.mkdir()
    (skills / "graph_analysis.md").write_text(SKILL_CONTENT, encoding="utf-8")
    (skills / "bug_detection.md").write_text(SKILL_CONTENT_2, encoding="utf-8")
    return skills


class TestSkillRouter:
    def test_route_matches_correct_skill(self, skills_dir: Path):
        result = SkillRouter(skills_dir).route("analyse architecture of the codebase")
        assert result.skill is not None
        assert result.skill.name == "graph_analysis"

    def test_route_no_match_returns_none(self, skills_dir: Path):
        result = SkillRouter(skills_dir).route("something completely unrelated xyz")
        assert result.skill is None
        assert result.confidence == 0.0

    def test_route_confidence_nonzero_on_match(self, skills_dir: Path):
        result = SkillRouter(skills_dir).route("detect bugs in the system")
        assert result.skill is not None
        assert result.confidence > 0.0

    def test_matched_triggers_populated(self, skills_dir: Path):
        result = SkillRouter(skills_dir).route("detect bugs")
        assert len(result.matched_triggers) > 0

    def test_list_skills_returns_all(self, skills_dir: Path):
        router = SkillRouter(skills_dir)
        skills = router.list_skills()
        assert len(skills) == 2

    def test_skill_execution_body_parsed(self, skills_dir: Path):
        router = SkillRouter(skills_dir)
        skills = router.list_skills()
        bodies = [s.execution_body for s in skills]
        assert any("Step 1" in b for b in bodies)

    def test_empty_skills_dir_no_match(self, tmp_path: Path):
        empty_dir = tmp_path / "empty_skills"
        empty_dir.mkdir()
        result = SkillRouter(empty_dir).route("analyse architecture")
        assert result.skill is None

    def test_malformed_skill_skipped(self, tmp_path: Path):
        """A skill file without YAML frontmatter is silently skipped."""
        skills = tmp_path / "skills"
        skills.mkdir()
        (skills / "bad.md").write_text("No frontmatter here.", encoding="utf-8")
        (skills / "graph_analysis.md").write_text(SKILL_CONTENT, encoding="utf-8")
        router = SkillRouter(skills)
        assert len(router.list_skills()) == 1

    def test_caching_does_not_reload(self, skills_dir: Path):
        router = SkillRouter(skills_dir)
        first = router.list_skills()
        second = router.list_skills()
        assert first is second  # same list object
