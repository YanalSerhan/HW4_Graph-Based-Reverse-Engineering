"""
CLI entry point for Reverse Engineering graph tool.
Wires CLI arguments -> SDK -> output, with no business logic of its own.
"""
import argparse
from pathlib import Path
from graph_rev_eng.sdk.sdk import ReverseEngineeringSDK
from graph_rev_eng.shared.config import ConfigManager

def main() -> None:
    parser = argparse.ArgumentParser(description="Reverse Engineering of Graph Knowledge Systems")
    parser.add_argument("--repo-url", type=str, help="GitHub URL to reverse engineer")
    parser.add_argument("--query", type=str, help="Query for the AI agents")
    parser.add_argument("--budget-tokens", type=int, default=8000, help="Token budget per session")
    parser.add_argument("--output-dir", type=str, default="results", help="Output directory")
    parser.add_argument("--compact", action="store_true", help="Trigger mid-session compaction")
    
    args = parser.parse_args()
    
    # Initialize config to validate startup
    _ = ConfigManager.get_instance()
    
    sdk = ReverseEngineeringSDK()
    
    if args.repo_url:
        print(f"Running SDK on repo: {args.repo_url}")
        sdk.run_grphify(args.repo_url)
        # Placeholder for further operations
        
if __name__ == "__main__":
    main()
