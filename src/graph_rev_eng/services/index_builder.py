"""
IndexBuilder — generates the LLM Wiki navigation artifacts from a Graph.

Rationale: separating index generation from graph loading keeps each class
focused. The IndexBuilder is the bridge between raw graph data and the
Obsidian-compatible markdown vault that agents navigate.

Output artifacts:
  - hot.md     : top-N hubs by degree centrality (primary agent entry)
  - index.md   : compact, structured entry point for Index-First Retrieval
  - /wiki/      : one markdown page per community (detailed analysis)
  - log.md     : traceability log of knowledge ingestion events
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from .graph_models import Graph
from .community_detector import Community

logger = logging.getLogger(__name__)

TOP_HUB_COUNT = 10   # Number of top nodes listed in hot.md


class IndexBuilder:
    """
    Builds the four-layer LLM Wiki from a Graph and detected Communities.

    Layer 1 — /raw:      graph.json (already produced by Grphify)
    Layer 2 — /wiki:     community pages with Obsidian Wikilinks
    Layer 3 — index.md:  compact entry point for Index-First Retrieval
    Layer 4 — log.md:    append-only ingestion traceability log
    """

    def build(
        self,
        graph: Graph,
        communities: list[Community],
        output_dir: Path,
    ) -> None:
        """
        Generates all wiki artifacts under output_dir.

        Creates subdirectories as needed. Overwrites existing files so every
        run reflects the latest graph state (idempotent).
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        wiki_dir = output_dir / "wiki"
        wiki_dir.mkdir(exist_ok=True)

        self._write_hot_md(graph, output_dir)
        self._write_index_md(graph, communities, output_dir)
        self._write_community_pages(graph, communities, wiki_dir)
        self._append_log(graph, output_dir)
        logger.info("Wiki artifacts written to %s", output_dir)

    def _write_hot_md(self, graph: Graph, output_dir: Path) -> None:
        """Writes hot.md listing the top hubs by total degree."""
        ranked = sorted(graph.nodes.values(), key=lambda n: graph.degree(n.node_id), reverse=True)
        top = ranked[:TOP_HUB_COUNT]
        lines = ["# Hot Nodes — Top Architectural Hubs\n"]
        lines.append(f"_Generated: {self._now()}_\n\n")
        lines.append("| Rank | Node | Type | Degree |\n")
        lines.append("|------|------|------|--------|\n")
        for rank, node in enumerate(top, start=1):
            deg = graph.degree(node.node_id)
            lines.append(f"| {rank} | [[{node.label}]] | {node.node_type} | {deg} |\n")
        (output_dir / "hot.md").write_text("".join(lines), encoding="utf-8")

    def _write_index_md(
        self, graph: Graph, communities: list[Community], output_dir: Path
    ) -> None:
        """Writes index.md — compact structural map for Index-First Retrieval."""
        lines = ["# Graph Index — Entry Point for Agents\n\n"]
        lines.append(f"_Graph: {len(graph.nodes)} nodes · {len(graph.edges)} edges_\n\n")
        lines.append("## Communities\n\n")
        for community in sorted(communities, key=lambda c: c.size, reverse=True):
            lines.append(
                f"- **{community.dominant_label}** ({community.size} nodes) "
                f"→ [[wiki/{community.dominant_label}]]\n"
            )
        lines.append("\n## Navigation\n\n")
        lines.append("- [[hot]] — Top hubs by centrality\n")
        lines.append("- [[log]] — Ingestion traceability log\n")
        (output_dir / "index.md").write_text("".join(lines), encoding="utf-8")

    def _write_community_pages(
        self, graph: Graph, communities: list[Community], wiki_dir: Path
    ) -> None:
        """Writes one markdown page per community to /wiki/."""
        for community in communities:
            page_name = community.dominant_label.replace("/", "_").replace("\\", "_")
            lines = [f"# Community: {community.dominant_label}\n\n"]
            lines.append(f"**Size:** {community.size} nodes | ")
            lines.append(f"**Cohesion:** {community.cohesion_ratio:.1%}\n\n")
            lines.append("## Nodes\n\n")
            for nid in sorted(community.node_ids):
                node = graph.get_node(nid)
                if node:
                    lines.append(f"- [[{node.label}]] (`{node.node_type}`)\n")
            (wiki_dir / f"{page_name}.md").write_text("".join(lines), encoding="utf-8")

    def _append_log(self, graph: Graph, output_dir: Path) -> None:
        """Appends an ingestion event to log.md for traceability."""
        log_path = output_dir / "log.md"
        entry = (
            f"\n## Ingestion — {self._now()}\n"
            f"- Nodes: {len(graph.nodes)}\n"
            f"- Edges: {len(graph.edges)}\n"
            f"- Hyperedges: {len(graph.hyperedges)}\n"
        )
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(entry)

    def _now(self) -> str:
        """Returns current UTC timestamp as ISO string."""
        return datetime.now(tz=timezone.utc).isoformat(timespec="seconds")
