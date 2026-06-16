"""
SkillRouter — selects the correct SKILL.md subgraph from a natural language query.

Rationale: loading the entire graph to answer every query is token-expensive.
The SkillRouter uses semantic trigger-phrase matching to select only the relevant
SKILL.md file and its associated subgraph, keeping retrieval well within the
skillListingBudgetFraction.

SKILL.md format expected:
  ---
  name: graph_analysis
  triggers:
    - analyse architecture
    - community detection
    - hub identification
  boundaries: graph.json must be loaded
  routing_subgraph: community_analysis
  ---
  [markdown execution body]
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import yaml  # pyyaml

logger = logging.getLogger(__name__)

SKILLS_DIR = Path("skills")
MIN_MATCH_SCORE = 1   # At least one trigger word must match


@dataclass
class Skill:
    """A parsed SKILL.md with its metadata and execution body."""

    name: str
    triggers: list[str]
    boundaries: str
    routing_subgraph: str
    execution_body: str
    source_path: Path


@dataclass
class RoutingResult:
    """Result of a SkillRouter.route() call."""

    skill: Skill | None
    confidence: float   # 0.0 – 1.0
    matched_triggers: list[str]


class SkillRouter:
    """
    Routes natural language queries to the most relevant SKILL.md.

    Skills are loaded lazily from SKILLS_DIR on first call and cached.
    Routing uses bag-of-words intersection between query tokens and trigger
    phrases — avoids vector store dependency while being transparent and testable.
    """

    def __init__(self, skills_dir: Path | None = None) -> None:
        self._skills_dir = skills_dir or SKILLS_DIR
        self._cache: list[Skill] | None = None

    def route(self, query: str) -> RoutingResult:
        """
        Returns the best-matching skill for the query.

        Returns RoutingResult with skill=None if no skill meets MIN_MATCH_SCORE.
        """
        skills = self._load_skills()
        if not skills:
            logger.warning("No skills found in %s", self._skills_dir)
            return RoutingResult(skill=None, confidence=0.0, matched_triggers=[])

        query_tokens = set(query.lower().split())
        best_skill: Skill | None = None
        best_score = 0
        best_matched: list[str] = []

        for skill in skills:
            score, matched = self._score_skill(skill, query_tokens)
            if score > best_score:
                best_score = score
                best_skill = skill
                best_matched = matched

        if best_score < MIN_MATCH_SCORE:
            logger.info("No skill matched query (best score: %d).", best_score)
            return RoutingResult(skill=None, confidence=0.0, matched_triggers=[])

        total_triggers = sum(len(s.triggers) for s in skills)
        confidence = min(1.0, best_score / max(total_triggers, 1))
        logger.info("Routed to skill '%s' (score=%d, confidence=%.2f)", best_skill.name, best_score, confidence)
        return RoutingResult(skill=best_skill, confidence=confidence, matched_triggers=best_matched)

    def list_skills(self) -> list[Skill]:
        """Returns all loaded skills — used by ContextBudgetManager for listing."""
        return self._load_skills()

    def _load_skills(self) -> list[Skill]:
        """Loads and caches all SKILL.md files from skills_dir."""
        if self._cache is not None:
            return self._cache
        self._cache = []
        if not self._skills_dir.exists():
            return self._cache
        for md_file in self._skills_dir.glob("*.md"):
            skill = self._parse_skill_file(md_file)
            if skill:
                self._cache.append(skill)
        logger.info("Loaded %d skills from %s", len(self._cache), self._skills_dir)
        return self._cache

    def _parse_skill_file(self, path: Path) -> Skill | None:
        """Parses YAML frontmatter and markdown body from a SKILL.md file."""
        try:
            content = path.read_text(encoding="utf-8")
            if not content.startswith("---"):
                logger.warning("Skill file %s missing YAML frontmatter.", path.name)
                return None
            parts = content.split("---", 2)
            if len(parts) < 3:
                return None
            frontmatter = yaml.safe_load(parts[1]) or {}
            body = parts[2].strip()
            return Skill(
                name=str(frontmatter.get("name", path.stem)),
                triggers=list(frontmatter.get("triggers", [])),
                boundaries=str(frontmatter.get("boundaries", "")),
                routing_subgraph=str(frontmatter.get("routing_subgraph", "")),
                execution_body=body,
                source_path=path,
            )
        except Exception as exc:
            logger.error("Failed to parse skill file %s: %s", path, exc)
            return None

    def _score_skill(self, skill: Skill, query_tokens: set[str]) -> tuple[int, list[str]]:
        """
        Scores a skill by counting trigger phrase token overlaps with query tokens.

        Returns (score, matched_trigger_phrases).
        """
        score = 0
        matched: list[str] = []
        for trigger in skill.triggers:
            trigger_tokens = set(trigger.lower().split())
            overlap = len(trigger_tokens & query_tokens)
            if overlap > 0:
                score += overlap
                matched.append(trigger)
        return score, matched
