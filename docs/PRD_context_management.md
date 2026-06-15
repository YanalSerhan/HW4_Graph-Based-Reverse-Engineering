# Mechanism PRD: Context Management

## 1. Theoretical Background
LLMs suffer from the "Lost in the Middle" phenomenon: when provided with large contexts (like massive chunks of source code), they accurately recall information at the beginning and end of the prompt but frequently ignore data in the middle. Furthermore, massive prompts bloat token costs and degrade inference latency. To solve this, we enforce a strict Context Budgeting Strategy.

## 2. Core Mechanisms

### 2.1 Index-First Retrieval
Instead of loading source files directly, the agent is forced to load `index.md` first. This file acts as a high-level map (generated from the `graph.json`). From `index.md`, the agent selects only 2–3 targeted sub-pages (e.g., a specific module or a specific skill) to load into its context.

### 2.2 Position-Aware Context Allocation
To defeat the "Lost in the Middle" problem, we construct the prompt strategically:
*   **Beginning (Edges):** Critical system prompts, hard rules, and safety guardrails.
*   **End (Edges):** The exact query or task to execute, ensuring it remains highly salient.
*   **Middle:** The retrieved subgraph data and source code context (the supporting detail).

### 2.3 The `/compact` Protocol
A mid-session summarization mechanism. When the token budget approaches 80% capacity during a long conversation, the system triggers `/compact`. The agent summarizes its current conversational state, decisions made, and intent into a concise block, flushing the raw conversational noise to free up the context window while preserving trajectory.

## 3. Specific I/O Requirements
*   **Input:** Current token count, agent conversational history, and retrieved document paths.
*   **Output:** A truncated/compacted context payload and a dynamically assembled prompt string obeying position-aware rules.

## 4. Constraints
*   `skillListingBudgetFraction`: A strict mathematical fraction of the context window reserved solely for presenting available tools/skills.
*   `Dropping Skill` Fallback: If context overflows, specific non-essential skills are dropped from the agent's view.

## 5. Alternative Approaches Considered
*   **Unlimited Context Window Loading:** Relying purely on models with 1M+ token windows (e.g., Gemini 1.5 Pro). Rejected because, while possible, it is cost-prohibitive, slower, and still occasionally susceptible to focus-loss on needle-in-a-haystack coding issues.
*   **Semantic Chunking (Vector DB):** Rejected as the primary retrieval method because vector databases chunk code arbitrarily, breaking syntactic units. Index-First retrieval preserves architectural boundaries.

## 6. Acceptance & Test Criteria
*   **Criteria 1:** A `ContextBudgetManager` successfully tracks tokens using a `TokenCounter` utility.
*   **Criteria 2:** If the context exceeds the threshold, the `/compact` protocol is triggered automatically.
*   **Criteria 3:** Critical rules (placed at prompt edges) are never truncated during compaction.
