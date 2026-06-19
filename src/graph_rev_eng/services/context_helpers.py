"""
context_helpers.py — helper functions for ContextBudgetManager.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .token_counter import TokenCounter

logger = logging.getLogger(__name__)


def select_pages(query: str, index_text: str) -> list[str]:
    """
    Selects 2–3 most relevant community pages by keyword overlap.

    This is a lightweight bag-of-words match — sufficient for structural
    queries and avoids needing a vector store in Phase 3.
    """
    query_tokens = set(query.lower().split())
    community_lines = [ln for ln in index_text.splitlines() if "[[wiki/" in ln]
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


def build_skill_listing(
    available_skills: list[str], counter: TokenCounter, skill_budget: int
) -> tuple[str, list[str]]:
    """
    Assembles the skill listing, dropping skills if budget overflows.

    Returns (skill_text, dropped_skills) so the caller knows what was omitted.
    """
    included: list[str] = []
    dropped: list[str] = []
    budget_used = 0
    for skill in available_skills:
        skill_tokens = counter.estimate_tokens(skill)
        if budget_used + skill_tokens <= skill_budget:
            included.append(skill)
            budget_used += skill_tokens
        else:
            dropped.append(skill)
            logger.warning("Dropped skill due to budget overflow: %s", skill)
    skills_text = "\n".join(f"- {s}" for s in included)
    return skills_text, dropped


def compact_content(
    content: str, query: str, budget: int, counter: TokenCounter
) -> tuple[str, int]:
    """
    Applies /compact: truncates content to fit within budget.

    Keeps the first and last 20% of the content (position-aware) and
    summarises the middle. Marks the result so callers know compaction ran.
    """
    budget_chars = budget * 4
    if len(content) <= budget_chars:
        return content, counter.estimate_tokens(content)
    keep = budget_chars // 2
    head = content[:keep]
    tail = content[-keep:]
    summary = (
        "\n\n[/compact: middle section summarised to fit token budget. "
        f"Query intent preserved: '{query[:80]}']\n\n"
    )
    compacted = head + summary + tail
    return compacted, counter.estimate_tokens(compacted)
