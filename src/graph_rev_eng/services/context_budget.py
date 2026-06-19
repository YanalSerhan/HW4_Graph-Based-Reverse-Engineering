"""
ContextBudgetManager — Index-First Retrieval with /compact and Dropping Skill.

Rationale: the "Lost in the Middle" problem means agents should receive the
most important context at the START and END of their prompt, with supporting
detail in the middle. This manager enforces that layout and hard token budgets,
preventing agents from accidentally exceeding their allocation.

Key mechanisms:
  1. Index-First Retrieval: load index.md → select 2–3 relevant community pages
  2. /compact protocol: mid-session summarisation to reset conversational noise
  3. Dropping Skill: gracefully omit skills when the budget overflows
  4. Position-aware assembly: critical rules at edges, detail in middle
"""

from __future__ import annotations

import logging
from pathlib import Path

from ..constants import DEFAULT_TOKEN_BUDGET
from .context_helpers import build_skill_listing, compact_content, select_pages
from .context_types import AssembledContext, FailureMode
from .token_counter import TokenCounter

logger = logging.getLogger(__name__)

SKILL_LISTING_FRACTION = 0.15  # 15% of budget reserved for skill listing
COMPACT_TRIGGER_RATIO = 0.80  # Trigger /compact when 80% of budget consumed


class ContextBudgetManager:
    """
    Manages context assembly within a hard token budget.

    All context passes through assemble() which enforces Index-First Retrieval,
    position-aware layout, and dropping skills when the budget overflows.
    """

    def __init__(
        self,
        wiki_dir: Path,
        token_counter: TokenCounter,
        budget: int = DEFAULT_TOKEN_BUDGET,
    ) -> None:
        self._wiki_dir = wiki_dir
        self._counter = token_counter
        self._budget = budget
        self._skill_budget = int(budget * SKILL_LISTING_FRACTION)
        self._session_consumed = 0

    def assemble(
        self,
        query: str,
        available_skills: list[str],
        critical_rules: str = "",
    ) -> AssembledContext:
        """
        Assembles a position-aware context for the given query.

        Layout: [critical_rules] + [index.md] + [selected pages] + [skill list]
        Critical rules and skills go at the edges; detail goes in the middle.
        """
        index_text = self._load_page("index.md")
        selected_pages = select_pages(query, index_text)
        page_texts = [self._load_page(f"wiki/{page}.md") for page in selected_pages]

        skills_text, dropped_skills = build_skill_listing(
            available_skills, self._counter, self._skill_budget
        )

        parts = []
        if critical_rules:
            parts.append(f"## Critical Rules\n{critical_rules}\n")
        parts.append(f"## Knowledge Base Index\n{index_text}\n")
        for i, text in enumerate(page_texts):
            parts.append(f"## Context Page {i + 1}\n{text}\n")
        parts.append(f"## Available Skills\n{skills_text}\n")

        content = "\n".join(parts)
        tokens = self._counter.estimate_tokens(content)

        if tokens > self._budget:
            content, tokens = compact_content(content, query, self._budget, self._counter)

        self._session_consumed += tokens
        failure_mode = self.detect_failure_mode(tokens)

        if failure_mode == FailureMode.OVERFLOW:
            logger.error(
                "Context OVERFLOW detected: %d tokens exceeds budget %d", tokens, self._budget
            )
        elif failure_mode == FailureMode.CONTEXT_ROT:
            logger.warning(
                "Context ROT detected: session consumed %d, triggering frequent compactions",
                self._session_consumed,
            )
        else:
            logger.info("Context assembled: %d tokens (budget %d)", tokens, self._budget)

        return AssembledContext(
            content=content,
            token_estimate=tokens,
            selected_pages=selected_pages,
            dropped_skills=dropped_skills,
            was_compacted=tokens < self._counter.estimate_tokens("\n".join(parts)),
        )

    def should_compact(self) -> bool:
        """Returns True when session consumption exceeds the compact trigger."""
        return self._session_consumed > self._budget * COMPACT_TRIGGER_RATIO

    def detect_failure_mode(self, last_assembly_tokens: int) -> FailureMode:
        """
        Detects the current health state of the context budget.

        Returns OVERFLOW if the last assembly exceeded the hard limit.
        Returns CONTEXT_ROT if the session is experiencing gradual decay (indicated by
        frequent compaction triggers).
        Otherwise returns NONE.
        """
        if last_assembly_tokens > self._budget:
            return FailureMode.OVERFLOW
        if self.should_compact():
            return FailureMode.CONTEXT_ROT
        return FailureMode.NONE

    def reset_session(self) -> None:
        """Resets session consumption counter — call between agent runs."""
        self._session_consumed = 0

    def _load_page(self, relative_path: str) -> str:
        """Loads a wiki page, returning empty string if the file does not exist."""
        path = self._wiki_dir / relative_path
        if path.exists():
            return path.read_text(encoding="utf-8")
        return f"[Page '{relative_path}' not found]"


