# Mechanism PRD: Agent Orchestration

## 1. Theoretical Background
Reverse engineering an entire codebase requires varied expertise—from safely fetching the code to extracting graph algorithms and verifying facts against raw source. A multi-agent framework separates these concerns, preventing context pollution and allowing specialized prompting per task. We utilize **CrewAI** to orchestrate these personas, leveraging its sequential and hierarchical task management features to drive the pipeline.

## 2. Agent Roles & Inter-Agent Communication
The process is executed by a crew of four specialized agents:

1.  **GitHub Downloader:**
    *   **Role:** Securely clone the repository and set up the local environment.
    *   **Outputs:** Validated repository path.
2.  **Graph Analyst:**
    *   **Role:** Analyzes `graph.json` and `index.md`, identifying hubs, bottlenecks, and defining communities without reading raw source code.
    *   **Outputs:** Architectural hypotheses and inferred edges.
3.  **Code Inspector:**
    *   **Role:** Grounds the Analyst's hypotheses by inspecting actual source files to confirm or dispute inferred edges.
    *   **Outputs:** Validation matrix (Confirmed vs. Ambiguous edges).
4.  **Report Writer:**
    *   **Role:** Synthesizes the final findings into a coherent Markdown report for human consumption.
    *   **Outputs:** `final_report.md`.

**Communication & Termination:**
Agents operate sequentially. The output of the Downloader feeds the Grphify process, which feeds the Analyst. The Analyst passes its hypotheses directly to the Code Inspector. Termination occurs when the Report Writer successfully commits `final_report.md` or if a safety guardrail (e.g., maximum token limit reached) triggers a hard stop.

## 3. Specific I/O Requirements
*   **Input:** Natural language query to the SDK (e.g., "Find all god-nodes in the FastAPI routing layer") and the repository URL.
*   **Output:** Coordinated task execution logs and the final markdown report containing synthesized insights.

## 4. Constraints
*   **Safety Guardrails:** Read-only actions (Graph traversal) are autonomous. Irreversible/dangerous actions require an explicit confirmation flag or are disabled completely via `model-invocation-disable`.
*   **Token Budget:** No single agent invocation can exceed its allocated token budget.

## 5. Alternative Approaches Considered
*   **LangGraph:** A highly capable, state-machine-based framework. Rejected in favor of CrewAI due to CrewAI's simpler abstraction for role-playing personas and its out-of-the-box sequential processing, which perfectly maps to our pipeline (Clone -> Extract -> Analyze -> Report).
*   **Monolithic LLM Agent:** Rejected because a single agent trying to hold the graph, the code, and the reporting context simultaneously would immediately hit the context-window ceiling.

## 6. Acceptance & Test Criteria
*   **Criteria 1:** CrewAI instantiates the four agents successfully with distinct goals and backstories.
*   **Criteria 2:** The pipeline can be interrupted safely if the `CodeInspector` exceeds the token budget.
*   **Criteria 3:** The `ReportWriter` successfully generates a `final_report.md` combining graph data and code data.
