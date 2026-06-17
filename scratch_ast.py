from pathlib import Path
from src.graph_rev_eng.services.ast_parser import ASTGraphBuilder
import json
from dataclasses import asdict

repo_path = Path("data/broken-python")
graph = ASTGraphBuilder().build(repo_path)

nodes_json = []
for v in graph.nodes.values():
    d = asdict(v)
    d["id"] = d.pop("node_id")
    d["type"] = d.pop("node_type")
    nodes_json.append(d)
    
edges_json = []
for e in graph.edges:
    d = asdict(e)
    d["source"] = d.pop("source_id")
    d["target"] = d.pop("target_id")
    d["type"] = d.pop("edge_type")
    edges_json.append(d)

output_path = Path("results/graph.json")
output_path.parent.mkdir(exist_ok=True)
with open(output_path, "w", encoding="utf-8") as f:
    json.dump({
        "nodes": nodes_json,
        "edges": edges_json,
        "hyperedges": [],
        "metadata": {}
    }, f, indent=2)

print("--- NODES ---")
for node in graph.nodes.values():
    print(f"[{node.node_type}] {node.node_id}")
