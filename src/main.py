"""
CLI entry point for the Reverse Engineering SDK.
"""

import argparse
import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

from graph_rev_eng.sdk.sdk import ReverseEngineeringSDK
from graph_rev_eng.services.ast_parser import ASTGraphBuilder
from graph_rev_eng.services.github_downloader import GitHubDownloaderAgent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="AI-powered graph-based reverse engineering pipeline."
    )
    parser.add_argument(
        "--repo-url",
        required=True,
        help="GitHub URL of the target repository to analyze.",
    )
    parser.add_argument(
        "--query",
        default="What are the main architectural issues in this codebase?",
        help="Natural language query for the agents.",
    )
    parser.add_argument(
        "--output-dir",
        default="results",
        help="Directory to write outputs (e.g. graph.json). Default: results/",
    )
    return parser

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # 1. Clone the repo
    print(f"\n[1/4] Cloning repository: {args.repo_url}")
    downloader = GitHubDownloaderAgent()
    repo_path = downloader.run(args.repo_url)
    print(f"      Cloned to: {repo_path}")

    # 2. Run AST parser -> graph.json
    print("\n[2/4] Running AST Parser to build architectural graph...")
    graph = ASTGraphBuilder().build(repo_path)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    graph_path = out_dir / "graph.json"

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
        # Keep edge_type instead of popping it to type
        edges_json.append(d)

    with open(graph_path, "w", encoding="utf-8") as f:
        json.dump({
            "nodes": nodes_json,
            "edges": edges_json,
            "hyperedges": [],
            "metadata": {}
        }, f, indent=2)
    print(f"      Saved graph to: {graph_path}")

    # 3. Build Obsidian vault -> obsidian/
    print("\n[3/4] Building Obsidian Vault...")
    try:
        # Run the existing script which we know works well
        subprocess.run([sys.executable, "generate_obsidian.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"      Error generating Obsidian vault: {e}")

    # 4. Run full AgentCrew pipeline
    print("\n[4/4] Running AgentCrew pipeline...")
    sdk = ReverseEngineeringSDK()
    report_path = out_dir / "final_report.md"

    pipeline_result = sdk.run_agents(
        task=args.query,
        github_url=args.repo_url,
        graph_path=graph_path,
        report_path=report_path,
    )

    # 5. Print Summary
    print("\n" + "="*50)
    print(" REVERSE ENGINEERING PIPELINE SUMMARY")
    print("="*50)
    print(f" Nodes found:          {len(graph.nodes)}")
    print(f" Edges found:          {len(graph.edges)}")
    print(f" Bugs detected:        {pipeline_result.bug_count}")
    print(f" Output files written: {graph_path}, obsidian/ (vault), {report_path}")
    print("\n Token Usage:")
    for agent, tokens in pipeline_result.token_summary.items():
        print(f"   - {agent}: {tokens}")
    print("="*50)

if __name__ == "__main__":
    main()
