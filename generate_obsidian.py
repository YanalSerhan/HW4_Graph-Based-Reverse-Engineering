import sys
from pathlib import Path

sys.path.insert(0, str(Path("src").resolve()))

from graph_rev_eng.services.agents.bug_detector import ArchitecturalBugDetector
from graph_rev_eng.services.community_detector import CommunityDetector
from graph_rev_eng.services.graph_loader import GraphLoader
from graph_rev_eng.services.token_counter import TokenCounter


def get_clean_label(node):
    if node.node_type == "error":
        if "Missing parentheses" in node.label:
            return "error-mathsquiz-syntax"
        elif "invalid syntax" in node.label:
            return "error-polygons-syntax"
    return node.label


def main():
    obsidian_dir = Path("obsidian")
    obsidian_dir.mkdir(exist_ok=True)

    loader = GraphLoader()
    graph = loader.load(Path("results/graph.json"))

    cd = CommunityDetector()
    communities = cd.detect(graph)

    counter = TokenCounter()
    detector = ArchitecturalBugDetector(counter)
    bugs = detector.process((graph, communities))

    # Sort nodes by degree
    all_nodes = sorted(graph.nodes.values(), key=lambda n: graph.degree(n.node_id), reverse=True)

    # --- index.md ---
    index_md = [
        "# Index",
        "",
        "## Communities",
        "| Community | Size | Cohesion | Top 3 Nodes |",
        "|---|---|---|---|",
    ]
    for c in communities:
        nodes = sorted(c.node_ids, key=lambda nid: graph.degree(nid), reverse=True)
        top3 = [f"[[{get_clean_label(graph.get_node(nid))}]]" for nid in nodes[:3]]
        index_md.append(
            f"| [[{c.dominant_label}]] | {c.size} | {c.cohesion_ratio:.0%} | {', '.join(top3)} |"
        )

    index_md.extend(["", "## Hubs", "| Hub Node | Degree |", "|---|---|"])

    unique_hubs = {}
    for n in all_nodes:
        deg = graph.degree(n.node_id)
        if deg > 0:
            lbl = get_clean_label(n)
            if lbl not in unique_hubs or deg > unique_hubs[lbl]:
                unique_hubs[lbl] = deg

    sorted_unique_hubs = sorted(unique_hubs.items(), key=lambda x: x[1], reverse=True)
    for lbl, deg in sorted_unique_hubs:
        index_md.append(f"| [[{lbl}]] | {deg} |")

    index_md.extend(
        [
            "",
            "## Navigation",
            "- [[hot]]",
        ]
    )
    for c in communities:
        index_md.append(f"- [[{c.dominant_label}]]")

    index_md.extend(
        [
            "",
            "## Detected Bugs",
        ]
    )
    for b in bugs:
        index_md.append(f"- **{b.bug_type}** ({b.severity}): {b.description}")

    (obsidian_dir / "index.md").write_text("\n".join(index_md), encoding="utf-8")

    # --- hot.md ---
    hot_md = ["# Hot Nodes & Bug Investigation", "", "## Top 5 Hubs"]
    for i, (lbl, deg) in enumerate(sorted_unique_hubs[:5], 1):
        hot_md.append(f"{i}. [[{lbl}]] (Degree: {deg})")

    hot_md.extend(["", "## Source Code: mathsquiz.py", "```python"])

    mathsquiz_path = Path("data/broken-python/mathsquiz/mathsquiz.py")
    if mathsquiz_path.exists():
        hot_md.append(mathsquiz_path.read_text(encoding="utf-8"))
    else:
        hot_md.append("# File not found")

    hot_md.extend(
        [
            "```",
            "",
            "## Root Cause Analysis",
            "The following architectural and logic issues were detected:",
            "",
        ]
    )

    for b in bugs:
        hot_md.extend(
            [
                f"### {b.bug_type}",
                f"- **Description:** {b.description}",
                f"- **Fix / Recommendation:** {b.recommendation}",
                "",
            ]
        )

    hot_md.extend(["## Navigation", "Return to [[index]]"])

    (obsidian_dir / "hot.md").write_text("\n".join(hot_md), encoding="utf-8")

    # --- Community Pages ---
    for c in communities:
        comm_md = [
            f"# Community: {c.dominant_label}",
            "",
            f"**Size:** {c.size} nodes",
            f"**Cohesion:** {c.cohesion_ratio:.0%}",
            "",
            "## Members",
        ]
        for nid in sorted(c.node_ids, key=lambda n: graph.degree(n), reverse=True):
            node = graph.get_node(nid)
            comm_md.append(f"- [[{get_clean_label(node)}]] (Degree: {graph.degree(nid)})")

        comm_md.extend(["", "## Navigation", "Return to [[index]]"])
        (obsidian_dir / f"{c.dominant_label}.md").write_text("\n".join(comm_md), encoding="utf-8")

    print("Obsidian vault generated successfully.")


if __name__ == "__main__":
    main()
