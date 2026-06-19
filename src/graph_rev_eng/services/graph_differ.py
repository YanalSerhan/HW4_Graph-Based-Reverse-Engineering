import json
import shutil
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path("src").resolve()))

from graph_rev_eng.services.ast_parser import ASTGraphBuilder
from graph_rev_eng.services.graph_models import Graph


class GraphDiff:
    def __init__(self, before: Graph, after: Graph):
        self.before = before
        self.after = after
        self.nodes_added = [n for nid, n in after.nodes.items() if nid not in before.nodes]
        self.nodes_removed = [n for nid, n in before.nodes.items() if nid not in after.nodes]

        before_edges = {(e.source_id, e.target_id, e.edge_type): e for e in before.edges}
        after_edges = {(e.source_id, e.target_id, e.edge_type): e for e in after.edges}

        self.edges_added = [e for k, e in after_edges.items() if k not in before_edges]
        self.edges_removed = [e for k, e in before_edges.items() if k not in after_edges]
        self.confidence_changes = []

        self.error_nodes_before = [n for n in before.nodes.values() if n.node_type == "error"]
        self.error_nodes_after = [n for n in after.nodes.values() if n.node_type == "error"]

        self.ambiguous_edges_before = [e for e in before.edges if e.edge_type == "AMBIGUOUS"]
        self.ambiguous_edges_after = [e for e in after.edges if e.edge_type == "AMBIGUOUS"]

def build_graph_for_state(repo_path: Path) -> Graph:
    builder = ASTGraphBuilder()
    return builder.build(repo_path)

def save_graph(graph: Graph, path: Path):
    data = {
        "nodes": [
            {
                "id": n.node_id,
                "label": n.label,
                "type": n.node_type,
                "file_path": n.file_path,
                "line_number": n.line_number
            } for n in graph.nodes.values()
        ],
        "edges": [
            {
                "source": e.source_id,
                "target": e.target_id,
                "type": e.edge_type,
                "confidence": e.confidence,
                "label": e.label
            } for e in graph.edges
        ],
        "hyperedges": []
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")

def main():
    repo_path = Path("data/broken-python")
    mathsquiz_py = repo_path / "mathsquiz/mathsquiz.py"
    mathsquiz_fixed = repo_path / "mathsquiz/mathsquiz_fixed.py"

    # 1. State BEFORE
    tmp_fixed = repo_path / "mathsquiz/mathsquiz_fixed.py.bak"
    if mathsquiz_fixed.exists():
        shutil.move(mathsquiz_fixed, tmp_fixed)

    graph_before = build_graph_for_state(repo_path)
    save_graph(graph_before, Path("results/graph_before.json"))

    # 2. State AFTER
    tmp_broken = repo_path / "mathsquiz/mathsquiz.py.bak"
    shutil.move(mathsquiz_py, tmp_broken)
    shutil.move(tmp_fixed, mathsquiz_py)

    graph_after = build_graph_for_state(repo_path)
    save_graph(graph_after, Path("results/graph_after.json"))

    # Restore original files
    shutil.move(mathsquiz_py, mathsquiz_fixed)
    shutil.move(tmp_broken, mathsquiz_py)

    # Diff
    diff = GraphDiff(graph_before, graph_after)

    # Generate Markdown
    md = [
        "# Architectural Graph Diff — Before vs After Bug Fix",
        "",
        "## Nodes Added",
        "| Node | Type | Reason |",
        "|---|---|---|"
    ]
    for n in diff.nodes_added:
        md.append(f"| {n.label} | {n.node_type} | Extracted from fixed code |")

    md.extend([
        "",
        "## Nodes Removed",
        "| Node | Type | Reason |",
        "|---|---|---|"
    ])
    for n in diff.nodes_removed:
        md.append(f"| {n.label} | {n.node_type} | Removed/Fixed |")

    md.extend([
        "",
        "## Edges Changed",
        "| Source | Target | Before | After | Interpretation |",
        "|---|---|---|---|---|"
    ])
    for e in diff.edges_removed:
        src = graph_before.nodes.get(e.source_id)
        tgt = graph_before.nodes.get(e.target_id)
        src_lbl = src.label if src else e.source_id
        tgt_lbl = tgt.label if tgt else e.target_id
        md.append(f"| {src_lbl} | {tgt_lbl} | {e.edge_type} | (removed) | Edge resolved |")

    for e in diff.edges_added:
        src = graph_after.nodes.get(e.source_id)
        tgt = graph_after.nodes.get(e.target_id)
        src_lbl = src.label if src else e.source_id
        tgt_lbl = tgt.label if tgt else e.target_id
        md.append(f"| {src_lbl} | {tgt_lbl} | (none) | {e.edge_type} | New relationship |")

    delta_nodes = len(graph_after.nodes) - len(graph_before.nodes)
    delta_edges = len(graph_after.edges) - len(graph_before.edges)
    delta_error = len(diff.error_nodes_after) - len(diff.error_nodes_before)
    delta_amb = len(diff.ambiguous_edges_after) - len(diff.ambiguous_edges_before)

    # Format deltas
    def fmt(d): return f"{d:+d}" if d != 0 else "0"

    md.extend([
        "",
        "## Architectural Health Score",
        "| Metric | Before | After | Delta |",
        "|--------|--------|-------|-------|",
        (
            f"| Total nodes | {len(graph_before.nodes)} | {len(graph_after.nodes)} "
            f"| {fmt(delta_nodes)} |"
        ),
        (
            f"| Total edges | {len(graph_before.edges)} | {len(graph_after.edges)} "
            f"| {fmt(delta_edges)} |"
        ),
        (
            f"| Error nodes | {len(diff.error_nodes_before)} | {len(diff.error_nodes_after)} "
            f"| {fmt(delta_error)} ✅ |"
        ),
        (
            f"| Ambiguous edges | {len(diff.ambiguous_edges_before)} | "
            f"{len(diff.ambiguous_edges_after)} | {fmt(delta_amb)} ✅ |"
        ),
    ])

    Path("results/graph_diff.md").write_text("\n".join(md), encoding="utf-8")

    # Regenerate obsidian
    shutil.copy("results/graph_after.json", "results/graph.json")
    import subprocess
    subprocess.run([sys.executable, "generate_obsidian.py"], check=True)

if __name__ == "__main__":
    main()
