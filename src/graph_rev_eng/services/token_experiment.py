import json
import os
import urllib.error
import urllib.request
from pathlib import Path


def call_openai(prompt: str) -> tuple[int, int]:
    api_key = os.environ.get("LLM_API_KEY")
    if not api_key:
        env_path = Path(".env")
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("LLM_API_KEY="):
                    api_key = line.split("=", 1)[1].strip()
                    break
    if not api_key:
        raise ValueError("LLM_API_KEY environment variable not set.")

    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 500,
    }

    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode("utf-8")
            res_json = json.loads(res_body)

            usage = res_json.get("usage", {})
            in_toks = usage.get("prompt_tokens", 0)
            out_toks = usage.get("completion_tokens", 0)
            return in_toks, out_toks
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        print(f"Error: {err_msg}")
        raise


def main():
    query = "What are the main architectural issues in this codebase?"

    # Scenario A: Naive RAG (All python files)
    naive_content = ""
    for p in Path("data/broken-python").rglob("*.py"):
        naive_content += f"\n\n--- {p.name} ---\n"
        naive_content += p.read_text(encoding="utf-8")

    prompt_a = f"{query}\n\nCodebase:\n{naive_content}"

    print("Running Scenario A (Naive RAG)...")
    in_a, out_a = call_openai(prompt_a)
    tot_a = in_a + out_a
    cost_a = (in_a / 1_000_000) * 0.15 + (out_a / 1_000_000) * 0.60

    # Scenario B: Graph-guided
    graph_content = ""
    for p in [Path("obsidian/index.md"), Path("obsidian/hot.md")]:
        graph_content += f"\n\n--- {p.name} ---\n"
        if p.exists():
            graph_content += p.read_text(encoding="utf-8")

    prompt_b = f"{query}\n\nContext:\n{graph_content}"

    print("Running Scenario B (Graph-guided)...")
    in_b, out_b = call_openai(prompt_b)
    tot_b = in_b + out_b
    cost_b = (in_b / 1_000_000) * 0.15 + (out_b / 1_000_000) * 0.60

    # Calculate reduction
    def reduction(a, b):
        if a == 0:
            return 0.0
        return ((a - b) / a) * 100

    red_in = reduction(in_a, in_b)
    red_out = reduction(out_a, out_b)
    red_tot = reduction(tot_a, tot_b)
    red_cost = reduction(cost_a, cost_b)

    results = [
        "| Scenario | Input Tokens | Output Tokens | Total Tokens | Cost (USD) |",
        "|---|---|---|---|---|",
        f"| Naive RAG | {in_a} | {out_a} | {tot_a} | ${cost_a:.6f} |",
        f"| Graph-guided | {in_b} | {out_b} | {tot_b} | ${cost_b:.6f} |",
        f"| Reduction | {red_in:.1f}% | {red_out:.1f}% | {red_tot:.1f}% | {red_cost:.1f}% |",
    ]

    out_path = Path("results/token_analysis.md")
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text("\n".join(results), encoding="utf-8")
    print(f"Results written to {out_path}")


if __name__ == "__main__":
    main()
