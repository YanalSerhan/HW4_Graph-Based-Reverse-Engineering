"""Unit tests for token_counter.py — TokenCounter, TokenUsage."""

from __future__ import annotations

import pytest

from graph_rev_eng.services.token_counter import TokenCounter, TokenUsage


class TestTokenUsage:
    def test_total_tokens(self):
        usage = TokenUsage("AgentX", prompt_tokens=100, completion_tokens=50)
        assert usage.total_tokens == 150


class TestTokenCounter:
    def test_record_accumulates(self, token_counter: TokenCounter):
        token_counter.record(TokenUsage("A", 100, 50))
        token_counter.record(TokenUsage("A", 200, 75))
        assert token_counter.total_prompt_tokens == 300
        assert token_counter.total_completion_tokens == 125
        assert token_counter.total_tokens == 425

    def test_by_agent_filters(self, token_counter: TokenCounter):
        token_counter.record(TokenUsage("AgentA", 100, 50))
        token_counter.record(TokenUsage("AgentB", 200, 80))
        a_records = token_counter.by_agent("AgentA")
        assert len(a_records) == 1
        assert a_records[0].prompt_tokens == 100

    def test_summary_keys(self, token_counter: TokenCounter):
        token_counter.record(TokenUsage("X", 10, 5))
        summary = token_counter.summary()
        assert "total_prompt_tokens" in summary
        assert "total_completion_tokens" in summary
        assert "total_tokens" in summary
        assert "call_count" in summary
        assert summary["call_count"] == 1

    def test_reset_clears_records(self, token_counter: TokenCounter):
        token_counter.record(TokenUsage("A", 100, 50))
        token_counter.reset()
        assert token_counter.total_tokens == 0
        assert token_counter.summary()["call_count"] == 0

    def test_estimate_tokens_nonempty(self, token_counter: TokenCounter):
        count = token_counter.estimate_tokens("Hello world, this is a test.")
        assert count > 0

    def test_estimate_tokens_empty(self, token_counter: TokenCounter):
        count = token_counter.estimate_tokens("")
        assert count >= 0

    def test_empty_counter_summary(self, token_counter: TokenCounter):
        assert token_counter.total_tokens == 0
        assert token_counter.summary()["call_count"] == 0
