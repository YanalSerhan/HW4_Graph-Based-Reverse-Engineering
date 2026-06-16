"""Unit tests for index_builder.py — IndexBuilder."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.graph_rev_eng.services.index_builder import IndexBuilder
from src.graph_rev_eng.services.community_detector import CommunityDetector


class TestIndexBuilder:
    def test_build_creates_hot_md(self, simple_graph, tmp_path):
        communities = CommunityDetector().detect(simple_graph)
        IndexBuilder().build(simple_graph, communities, tmp_path)
        assert (tmp_path / "hot.md").exists()

    def test_build_creates_index_md(self, simple_graph, tmp_path):
        communities = CommunityDetector().detect(simple_graph)
        IndexBuilder().build(simple_graph, communities, tmp_path)
        assert (tmp_path / "index.md").exists()

    def test_build_creates_log_md(self, simple_graph, tmp_path):
        communities = CommunityDetector().detect(simple_graph)
        IndexBuilder().build(simple_graph, communities, tmp_path)
        assert (tmp_path / "log.md").exists()

    def test_build_creates_wiki_dir(self, simple_graph, tmp_path):
        communities = CommunityDetector().detect(simple_graph)
        IndexBuilder().build(simple_graph, communities, tmp_path)
        assert (tmp_path / "wiki").is_dir()

    def test_hot_md_contains_wikilinks(self, simple_graph, tmp_path):
        communities = CommunityDetector().detect(simple_graph)
        IndexBuilder().build(simple_graph, communities, tmp_path)
        content = (tmp_path / "hot.md").read_text()
        assert "[[" in content

    def test_index_md_contains_community_links(self, simple_graph, tmp_path):
        communities = CommunityDetector().detect(simple_graph)
        IndexBuilder().build(simple_graph, communities, tmp_path)
        content = (tmp_path / "index.md").read_text()
        assert "[[wiki/" in content

    def test_build_idempotent(self, simple_graph, tmp_path):
        """Running build twice should overwrite without errors."""
        communities = CommunityDetector().detect(simple_graph)
        builder = IndexBuilder()
        builder.build(simple_graph, communities, tmp_path)
        builder.build(simple_graph, communities, tmp_path)
        assert (tmp_path / "hot.md").exists()

    def test_log_md_appends_on_repeat(self, simple_graph, tmp_path):
        communities = CommunityDetector().detect(simple_graph)
        builder = IndexBuilder()
        builder.build(simple_graph, communities, tmp_path)
        builder.build(simple_graph, communities, tmp_path)
        content = (tmp_path / "log.md").read_text()
        assert content.count("## Ingestion") == 2

    def test_empty_graph_builds_without_error(self, empty_graph, tmp_path):
        IndexBuilder().build(empty_graph, [], tmp_path)
        assert (tmp_path / "index.md").exists()
