import json
import shutil
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path("src").resolve()))

from graph_rev_eng.services.ast_parser import ASTGraphBuilder
from graph_rev_eng.services.graph_differ_format import format_graph_diff
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
                "line_number": n.line_number,
            }
            for n in graph.nodes.values()
        ],
        "edges": [
            {
                "source": e.source_id,
                "target": e.target_id,
                "type": e.edge_type,
                "confidence": e.confidence,
                "label": e.label,
            }
            for e in graph.edges
        ],
        "hyperedges": [],
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
    md = format_graph_diff(diff, graph_before, graph_after)
    Path("results/graph_diff.md").write_text(md, encoding="utf-8")

    # Regenerate obsidian
    shutil.copy("results/graph_after.json", "results/graph.json")
    import subprocess

    subprocess.run([sys.executable, "generate_obsidian.py"], check=True)


if __name__ == "__main__":
    main()
