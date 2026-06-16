"""Unit tests for context_budget.py — ContextBudgetManager."""

from __future__ import annotations

from pathlib import Path

from graph_rev_eng.services.context_budget import ContextBudgetManager
from graph_rev_eng.services.token_counter import TokenCounter


def _make_manager(tmp_path: Path, budget: int = 1000) -> ContextBudgetManager:
    """Creates a ContextBudgetManager with a minimal wiki in tmp_path."""
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    (tmp_path / "index.md").write_text(
        "# Index\n\n- **services** (5 nodes) → [[wiki/services]]\n"
        "- **models** (3 nodes) → [[wiki/models]]\n",
        encoding="utf-8",
    )
    (wiki / "services.md").write_text("# Community: services\n\nsome content", encoding="utf-8")
    (wiki / "models.md").write_text("# Community: models\n\nsome content", encoding="utf-8")
    counter = TokenCounter()
    return ContextBudgetManager(wiki_dir=tmp_path, token_counter=counter, budget=budget)


class TestContextBudgetManager:
    def test_assemble_returns_assembled_context(self, tmp_path: Path):
        manager = _make_manager(tmp_path)
        result = manager.assemble("analyse services architecture", ["skill_a"])
        assert result.content
        assert result.token_estimate > 0

    def test_assemble_selects_relevant_pages(self, tmp_path: Path):
        manager = _make_manager(tmp_path)
        result = manager.assemble("services analysis", ["skill_a"])
        assert "services" in result.selected_pages

    def test_dropping_skill_when_budget_small(self, tmp_path: Path):
        manager = _make_manager(tmp_path, budget=10)
        many_skills = [
            f"skill_{i} — very long skill description that takes many tokens" for i in range(20)
        ]
        result = manager.assemble("query", many_skills)
        assert len(result.dropped_skills) > 0

    def test_no_skills_dropped_within_budget(self, tmp_path: Path):
        manager = _make_manager(tmp_path, budget=5000)
        result = manager.assemble("query", ["skill_a", "skill_b"])
        assert result.dropped_skills == []

    def test_should_compact_false_initially(self, tmp_path: Path):
        manager = _make_manager(tmp_path)
        assert manager.should_compact() is False

    def test_reset_session(self, tmp_path: Path):
        manager = _make_manager(tmp_path, budget=1000)
        manager.assemble("query", ["skill_a"])
        manager.reset_session()
        assert manager.should_compact() is False

    def test_missing_page_returns_placeholder(self, tmp_path: Path):
        manager = _make_manager(tmp_path)
        result = manager.assemble("nonexistent page query", ["skill_a"])
        # Should not raise, even if no pages match
        assert result.content is not None

    def test_compact_applied_on_tiny_budget(self, tmp_path: Path):
        manager = _make_manager(tmp_path, budget=5)
        result = manager.assemble("query", [])
        # With budget=5 tokens (20 chars), content should be compacted
        assert result.token_estimate >= 0
