import contextlib
import json
import urllib.error
import urllib.request
from pathlib import Path

from ..shared.config import ConfigManager


def call_openai(prompt: str) -> tuple[int, int]:
    config = ConfigManager.get_instance()
    api_key = config.get_api_key("LLM_API_KEY")
    if not api_key:
        raise ValueError("LLM_API_KEY environment variable not set.")

    url = config.get_api_url()
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
    queries = [
        "What are the main architectural issues in this codebase?",
        "How is the ApiGatekeeper implemented?",
        "Where does the ContextBudgetManager calculate limits?",
        "Are there any circular dependencies between the services?",
        "How does the HubVsBottleneckClassifier handle cross-community ratios?"
    ]

    # Scenario A: Naive RAG (All python files)
    naive_content = ""
    for p in Path("data/broken-python").rglob("*.py"):
        naive_content += f"\n\n--- {p.name} ---\n"
        with contextlib.suppress(BaseException):
            naive_content += p.read_text(encoding="utf-8")

    # Scenario B: Graph-guided
    graph_content = ""
    for p in [Path("results/wiki/index.md"), Path("results/wiki/hot.md")]:
        graph_content += f"\n\n--- {p.name} ---\n"
        with contextlib.suppress(BaseException):
            graph_content += p.read_text(encoding="utf-8")

    results = [
        "| Query | Scenario | Input Tokens | Output Tokens | Total Tokens | Cost (USD) |",
        "|---|---|---|---|---|---|"
    ]

    tot_in_a = tot_out_a = tot_in_b = tot_out_b = 0

    for i, query in enumerate(queries, 1):
        prompt_a = f"{query}\n\nCodebase:\n{naive_content}"
        print(f"Running Query {i} Scenario A (Naive RAG)...")
        in_a, out_a = call_openai(prompt_a)
        tot_in_a += in_a
        tot_out_a += out_a
        cost_a = (in_a / 1_000_000) * 0.15 + (out_a / 1_000_000) * 0.60

        prompt_b = f"{query}\n\nContext:\n{graph_content}"
        print(f"Running Query {i} Scenario B (Graph-guided)...")
        in_b, out_b = call_openai(prompt_b)
        tot_in_b += in_b
        tot_out_b += out_b
        cost_b = (in_b / 1_000_000) * 0.15 + (out_b / 1_000_000) * 0.60

        results.append(
            f"| Q{i} | Naive RAG | {in_a} | {out_a} | {in_a+out_a} | ${cost_a:.6f} |"
        )
        results.append(
            f"| Q{i} | Graph-guided | {in_b} | {out_b} | {in_b+out_b} | ${cost_b:.6f} |"
        )

    def reduction(a, b):
        if a == 0:
            return 0.0
        return ((a - b) / a) * 100

    tot_a = tot_in_a + tot_out_a
    tot_b = tot_in_b + tot_out_b
    tot_cost_a = (tot_in_a / 1_000_000) * 0.15 + (tot_out_a / 1_000_000) * 0.60
    tot_cost_b = (tot_in_b / 1_000_000) * 0.15 + (tot_out_b / 1_000_000) * 0.60

    red_in = reduction(tot_in_a, tot_in_b)
    red_out = reduction(tot_out_a, tot_out_b)
    red_tot = reduction(tot_a, tot_b)
    red_cost = reduction(tot_cost_a, tot_cost_b)

    results.append("|---|---|---|---|---|---|")
    results.append(
        f"| **TOTAL** | Naive RAG | {tot_in_a} | {tot_out_a} | "
        f"{tot_a} | ${tot_cost_a:.6f} |"
    )
    results.append(
        f"| **TOTAL** | Graph-guided | {tot_in_b} | {tot_out_b} | "
        f"{tot_b} | ${tot_cost_b:.6f} |"
    )
    results.append(
        f"| **Reduction** | - | **{red_in:.1f}%** | **{red_out:.1f}%** | "
        f"**{red_tot:.1f}%** | **{red_cost:.1f}%** |"
    )

    out_path = Path("results/token_analysis.md")
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text("\n".join(results), encoding="utf-8")
    print(f"Results written to {out_path}")


if __name__ == "__main__":
    main()
