"""
CLI entry point for the Reverse Engineering SDK.

No business logic lives here — all calls go through ReverseEngineeringSDK.
Follows Nielsen's heuristic #5 (error prevention) with clear flag descriptions
and #9 (help and documentation) with rich --help output.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    """Builds and returns the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="graph-rev-eng",
        description=(
            "AI-powered graph-based reverse engineering of Python codebases.\n"
            "Uses Grphify + multi-agent analysis to extract architectural insights."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--repo-url",
        metavar="URL",
        default="",
        help="GitHub URL of the target repository to clone and analyse.",
    )
    parser.add_argument(
        "--query",
        metavar="TEXT",
        default="",
        help="Natural language query to route to the appropriate skill.",
    )
    parser.add_argument(
        "--budget-tokens",
        type=int,
        default=8000,
        metavar="N",
        help="Maximum total tokens to use across all agent invocations. Default: 8000.",
    )
    parser.add_argument(
        "--output-dir",
        metavar="DIR",
        default="results",
        help="Directory to write outputs (graph.json, wiki, report). Default: results/.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Trigger /compact mid-session context summarisation before running agents.",
    )
    parser.add_argument(
        "--graph-path",
        metavar="FILE",
        default="",
        help="Path to an existing graph.json (skips Grphify scan).",
    )
    return parser


def main() -> None:
    """Parses CLI arguments and delegates to the ReverseEngineeringSDK."""
    parser = build_parser()
    args = parser.parse_args()

    # Late import keeps startup fast and avoids circular-import risks at module level
    from graph_rev_eng.sdk.sdk import ReverseEngineeringSDK

    sdk = ReverseEngineeringSDK()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.query:
        result = sdk.route_skill(args.query)
        if result.skill:
            print(f"Skill matched: {result.skill.name} (confidence: {result.confidence:.0%})")
            print(f"Matched triggers: {result.matched_triggers}")
        else:
            print("No skill matched the query.")
        return

    if args.repo_url or args.graph_path:
        graph_path = Path(args.graph_path) if args.graph_path else None
        graph_html_path = None
        graph_report_path = None
        if args.repo_url and not graph_path:
            graph_path, graph_html_path, graph_report_path = sdk.run_grphify(args.repo_url)

        pipeline_result = sdk.run_agents(
            task="full-analysis",
            github_url=args.repo_url,
            graph_path=graph_path,
            graph_html_path=graph_html_path,
            graph_report_path=graph_report_path,
            report_path=output_dir / "final_report.md",
        )
        print(json.dumps(pipeline_result.token_summary, indent=2))
        print(f"Report: {pipeline_result.report_path}")
        if pipeline_result.errors:
            print("Errors:", pipeline_result.errors, file=sys.stderr)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
