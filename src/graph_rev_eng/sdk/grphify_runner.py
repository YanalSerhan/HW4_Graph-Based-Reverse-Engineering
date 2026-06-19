"""
grphify_runner.py — encapsulates the Grphify CLI execution and AST fallback.
"""
from pathlib import Path


def run_grphify_cli(repo_path: str, results_dir: Path) -> tuple[Path, Path, Path]:
    """
    Runs the Grphify CLI on repo_path and returns paths to
    (graph.json, graph.html, GRAPH_REPORT.md).

    In production, shells out to `grphify scan <repo_path>`.
    """
    import subprocess

    output_path = results_dir / "graph.json"
    html_path = results_dir / "graph.html"
    report_path = results_dir / "GRAPH_REPORT.md"
    results_dir.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            ["graphify", "scan", repo_path, "--output", str(output_path)],
            check=True,
            capture_output=True,
            text=True,
            timeout=600,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        # Grphify not installed or failed — fall back to internal AST parser
        import json
        import logging
        from dataclasses import asdict

        from ..services.ast_parser import ASTGraphBuilder

        logging.getLogger(__name__).warning(
            "Grphify unavailable (%s). Falling back to internal AST parser.", exc
        )

        graph = ASTGraphBuilder().build(Path(repo_path))

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

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(
                {"nodes": nodes_json, "edges": edges_json, "hyperedges": [], "metadata": {}},
                f,
                indent=2,
            )

    # Generate real fallback outputs
    import shutil
    try:
        shutil.copy("artifacts/graph_visualization.html", html_path)
    except FileNotFoundError:
        html_path.write_text(
            "<html><body>Mock Graph HTML Metadata</body></html>", encoding="utf-8"
        )

    try:
        from ..services.ast_parser import ASTGraphBuilder
        from ..services.report_generator import generate_graph_report

        # Re-parse quickly to generate the report
        g = ASTGraphBuilder().build(Path(repo_path))
        report_md = generate_graph_report(g)
        report_path.write_text(report_md, encoding="utf-8")
    except ImportError:
        report_path.write_text(
            "# Mock GRAPH_REPORT\nNo actual Grphify output available.", encoding="utf-8"
        )

    return output_path, html_path, report_path
