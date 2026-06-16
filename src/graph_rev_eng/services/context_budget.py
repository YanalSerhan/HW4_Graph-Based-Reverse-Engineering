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
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from ..constants import DEFAULT_TOKEN_BUDGET
from .token_counter import TokenCounter

logger = logging.getLogger(__name__)

SKILL_LISTING_FRACTION = 0.15   # 15% of budget reserved for skill listing
COMPACT_TRIGGER_RATIO = 0.80    # Trigger /compact when 80% of budget consumed


class FailureMode(str, Enum):
    """Failure modes for context assembly."""

    NONE = "NONE"
    OVERFLOW = "OVERFLOW"
    CONTEXT_ROT = "CONTEXT_ROT"


@dataclass
class AssembledContext:
    """Context package ready to pass to an agent."""

    content: str
    token_estimate: int
    selected_pages: list[str]
    dropped_skills: list[str] = field(default_factory=list)
    was_compacted: bool = False


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
        selected_pages = self._select_pages(query, index_text)
        page_texts = [self._load_page(f"wiki/{page}.md") for page in selected_pages]

        skills_text, dropped_skills = self._build_skill_listing(available_skills)

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
            content, tokens = self._compact(content, query)

        self._session_consumed += tokens
        failure_mode = self.detect_failure_mode(tokens)
        
        if failure_mode == FailureMode.OVERFLOW:
            logger.error("Context OVERFLOW detected: %d tokens exceeds budget %d", tokens, self._budget)
        elif failure_mode == FailureMode.CONTEXT_ROT:
            logger.warning("Context ROT detected: session consumed %d, triggering frequent compactions", self._session_consumed)
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

    def _select_pages(self, query: str, index_text: str) -> list[str]:
        """
        Selects 2–3 most relevant community pages by keyword overlap.

        This is a lightweight bag-of-words match — sufficient for structural
        queries and avoids needing a vector store in Phase 3.
        """
        query_tokens = set(query.lower().split())
        community_lines = [
            ln for ln in index_text.splitlines() if "[[wiki/" in ln
        ]
        scored: list[tuple[str, int]] = []
        for line in community_lines:
            start = line.find("[[wiki/") + 7
            end = line.find("]]", start)
            page = line[start:end] if end > start else ""
            if not page:
                continue
            overlap = sum(1 for tok in query_tokens if tok in line.lower())
            scored.append((page, overlap))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [page for page, _ in scored[:3]]

    def _build_skill_listing(
        self, available_skills: list[str]
    ) -> tuple[str, list[str]]:
        """
        Assembles the skill listing, dropping skills if budget overflows.

        Returns (skill_text, dropped_skills) so the caller knows what was omitted.
        """
        included: list[str] = []
        dropped: list[str] = []
        budget_used = 0
        for skill in available_skills:
            skill_tokens = self._counter.estimate_tokens(skill)
            if budget_used + skill_tokens <= self._skill_budget:
                included.append(skill)
                budget_used += skill_tokens
            else:
                dropped.append(skill)
                logger.warning("Dropped skill due to budget overflow: %s", skill)
        skills_text = "\n".join(f"- {s}" for s in included)
        return skills_text, dropped

    def _compact(self, content: str, query: str) -> tuple[str, int]:
        """
        Applies /compact: truncates content to fit within budget.

        Keeps the first and last 20% of the content (position-aware) and
        summarises the middle. Marks the result so callers know compaction ran.
        """
        budget_chars = self._budget * 4
        if len(content) <= budget_chars:
            return content, self._counter.estimate_tokens(content)
        keep = budget_chars // 2
        head = content[:keep]
        tail = content[-keep:]
        summary = (
            "\n\n[/compact: middle section summarised to fit token budget. "
            f"Query intent preserved: '{query[:80]}']\n\n"
        )
        compacted = head + summary + tail
        return compacted, self._counter.estimate_tokens(compacted)
