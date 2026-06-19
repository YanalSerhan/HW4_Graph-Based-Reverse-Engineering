import sys
from pathlib import Path

sys.path.insert(0, str(Path("src").resolve()))

from graph_rev_eng.services.graph_loader import GraphLoader
from graph_rev_eng.services.llm import OpenAILLM
from graph_rev_eng.shared.config import ConfigManager
from graph_rev_eng.shared.gatekeeper import ApiGatekeeper, RateLimitConfig

FACTS = [
    ("mathsquiz-step2.py calls ask_question", True),
    ("polygons.py imports turtle", True),
    ("mathsquiz.py calls randint", False),
    ("mathsquiz-step3.py calls welcome_message", True),
    ("mathsquiz-step2.py calls print_final_scores", True),
    ("mathsquiz-step3.py calls print_final_scores", True),
    ("mathsquiz-step3.py calls randint", True),
    ("mathsquiz-step3.py imports random", True),
    ("mathsquiz.py has a Missing parentheses error", True),
    ("polygons.py has a SyntaxError", True),
    ("ask_question is defined in mathsquiz-step2.py", True),
    ("welcome_message is defined in mathsquiz-step3.py", True),
    ("polygons.py calls ask_question", False),
    ("polygons.py imports random", False),
    ("mathsquiz-step2.py calls randint", False),
    ("mathsquiz-step2.py imports random", False),
    ("mathsquiz-step3.py imports turtle", False),
    ("welcome_message is defined in polygons.py", False),
    ("print_final_scores is defined in mathsquiz.py", False),
    ("mathsquiz.py calls ask_question", False),
]

def main():
    repo_path = Path("data/broken-python")
    graph_path = Path("results/graph.json")

    config = ConfigManager.get_instance()
    gatekeeper = ApiGatekeeper(RateLimitConfig.from_dict(config.get_rate_limits()))
    llm = OpenAILLM(gatekeeper, config.get_api_key("LLM_API_KEY"))

    loader = GraphLoader()
    graph = loader.load(graph_path)

    graph_context = "Graph Edges:\n"
    for e in graph.edges:
        graph_context += f"- {e.source_id} -> {e.target_id} ({e.label})\n"

    # Read source code to give the agent full ground truth capability
    source_context = ""
    for py_file in repo_path.rglob("*.py"):
        try:
            content = py_file.read_text(encoding="utf-8")
            source_context += f"\n--- {py_file.name} ---\n{content}\n"
        except Exception:
            pass

    tp = fp = tn = fn = 0

    results_md = [
        "# CodeInspectorAgent Confusion Matrix",
        "",
        "| Fact | Ground Truth | Agent Prediction | Result |",
        "|---|---|---|---|"
    ]

    print("Evaluating 20 architectural facts...")
    for fact, expected in FACTS:
        prompt = (
            f"You are the CodeInspectorAgent. Verify this architectural fact: '{fact}'.\n\n"
            f"Here is the project graph structure:\n{graph_context}\n\n"
            f"Here is the source code:\n{source_context}\n\n"
            "Based on the graph and source code, is this fact TRUE or FALSE? "
            "Reply with exactly one word: TRUE or FALSE."
        )

        response = llm(prompt).strip().upper()
        predicted = "TRUE" in response

        if expected and predicted:
            res = "TP"
            tp += 1
        elif expected and not predicted:
            res = "FN"
            fn += 1
        elif not expected and predicted:
            res = "FP"
            fp += 1
        else:
            res = "TN"
            tn += 1

        results_md.append(f"| {fact} | {expected} | {predicted} | {res} |")
        print(f"Fact: '{fact}' | Expected: {expected:<5} | Predicted: {predicted:<5} | {res}")

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    results_md.extend([
        "",
        "## Metrics",
        f"- **True Positives (TP):** {tp}",
        f"- **False Positives (FP):** {fp}",
        f"- **True Negatives (TN):** {tn}",
        f"- **False Negatives (FN):** {fn}",
        "",
        f"- **Precision:** {precision:.2f}",
        f"- **Recall:** {recall:.2f}",
        f"- **F1 Score:** {f1:.2f}"
    ])

    out_path = Path("results/confusion_matrix.md")
    out_path.parent.mkdir(exist_ok=True, parents=True)
    out_path.write_text("\n".join(results_md), encoding="utf-8")
    print(f"\nSaved confusion matrix to {out_path}")

if __name__ == "__main__":
    main()
