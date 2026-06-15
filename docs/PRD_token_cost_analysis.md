# Mechanism PRD: Token Cost Analysis

## 1. Theoretical Background
LLM APIs charge based on token volume (input tokens for the prompt, output tokens for the response). When processing large codebases, naive retrieval methods (passing entire files) quickly incur prohibitive costs. By utilizing Graph-Based Index-First Retrieval, we aggressively prune the input context. To prove the efficacy of this architecture, we must scientifically measure and compare the token footprint of the graph-based approach against a baseline naive approach.

## 2. Measurement Protocol
The system will implement a `TokenCounter` utility within the `ApiGatekeeper`. This utility wraps every LLM call, logging the exact token usage reported by the API.

### 2.1 Before/After Methodology
To validate the architecture, the following experiment must be run programmatically during Phase 6:
1.  **Baseline (Before Grphify):** Given a set of 5 standard architectural queries, load the raw source code of the relevant modules into the prompt and execute. Record input and output tokens.
2.  **Optimized (After Grphify):** For the same 5 queries, use Index-First Retrieval, loading only `index.md` and the 2 targeted sub-pages. Execute and record tokens.
3.  **Comparison:** Calculate the percentage reduction in input tokens.

### 2.2 Cost Breakdown Table
The final report must output a structured cost analysis table:

| Scenario | Model | Input Tokens | Output Tokens | Total Cost (USD) |
| :--- | :--- | :--- | :--- | :--- |
| Naive RAG (Query 1) | GPT-4o | 120,000 | 500 | $0.60 |
| Graph-Based (Query 1) | GPT-4o | 15,000 | 500 | $0.08 |
| **Reduction** | | **87.5%** | **0%** | **86.6%** |

## 3. Specific I/O Requirements
*   **Input:** Raw API response metadata containing `prompt_tokens` and `completion_tokens`.
*   **Output:** Continuous logging in `results/token_usage.log` and a finalized Markdown table in `results/token_analysis.md`.

## 4. Constraints
*   Token pricing metrics must be configurable (e.g., loaded from `config/setup.json` or `config/rate_limits.json`) so the system can adapt if API pricing changes.
*   Token measurement must not interfere with the primary execution thread (log asynchronously if possible).

## 5. Alternative Approaches Considered
*   **Estimating via Tiktoken:** Counting tokens locally before sending the request. Rejected as the primary measurement tool because different models use different tokenizers; the actual API response metadata is the ground truth for billing. Local counting will be used only for budget enforcement, not cost analysis.

## 6. Acceptance & Test Criteria
*   **Criteria 1:** `TokenCounter` successfully parses usage metadata from the LLM API response.
*   **Criteria 2:** Total token accumulation persists across a multi-agent execution session.
*   **Criteria 3:** The automated test runner generates the Cost Breakdown Table automatically based on mock data.
