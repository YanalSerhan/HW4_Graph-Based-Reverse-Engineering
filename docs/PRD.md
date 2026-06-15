# Product Requirements Document (PRD)

## 1. Project Overview
This project tackles the **Reverse Engineering Problem**: understanding a large, unfamiliar Python codebase systematically. Traditional naive approaches (e.g., simple RAG over all files) suffer from the "Lost in the Middle" problem, where the LLM forgets context due to massive token overhead. This system leverages an AI agent orchestration framework (CrewAI) integrated with **Grphify** (a static analysis graph generator) and **Obsidian** (a local knowledge base vault) to reverse-engineer software architectures efficiently.

## 2. Target User & Pain Points
*   **Target User:** Senior Software Engineers, Code Reviewers, and Architects onboarding onto or auditing legacy codebases.
*   **Pain Points:**
    *   **Context-Window Bottleneck:** Passing entire codebases into LLMs exceeds token limits.
    *   **"Lost in the Middle" Problem:** RAG models retrieving large chunks often lose critical context when it is buried in the middle of long prompts.
    *   **Architectural Obscurity:** It is difficult to distinguish "healthy hubs" from "god objects" or "Single Points of Failure" without a structured map.

## 3. Target Repository
*   **Repository:** `BugsInPy` (or equivalent non-trivial Python codebases included within it).
*   **Rationale:** Provides real-world, structured, and buggy codebases with existing ground truths for evaluation. It's complex enough to test community detection and hub identification, but structured enough to allow deterministic AST extraction via Grphify.

## 4. Measurable Goals (KPIs)
*   **Token Efficiency:** Achieve >70% token reduction compared to a naive RAG baseline when answering architectural queries.
*   **Agent Accuracy:** Achieve an F1-Score of >85% on a Confusion Matrix testing factual questions regarding architectural dependencies.
*   **Architectural Insights:** Automatically extract and document at least 5 meaningful architectural insights (e.g., identifying god-nodes, missing abstractions, or cyclic dependencies).

## 5. Requirements

### 5.1 Functional Requirements
*   **Graph Generation:** Generate an AST-derived property graph using the Grphify CLI, producing a `graph.json`.
*   **Community Detection:** Programmatically group files into related modules/communities using edge density.
*   **Hub/Bottleneck Identification:** Classify highly-connected nodes as either healthy architectural hubs or risky bottlenecks (SPOFs).
*   **Traceability:** Map PRD requirements (annotated with `WHY`/`TODO`/`NOTE`) to their corresponding implementation nodes.
*   **Agent-Driven Bug/Smell Detection:** Identify structural anti-patterns autonomously.

### 5.2 Non-Functional Requirements
*   **Performance:** High token efficiency via Index-First Retrieval and context budgeting.
*   **Security:** Zero hardcoded secrets; strictly use `os.environ` and `.env`.
*   **Reliability:** Deterministic AST extraction logic; strict rate-limit handling via an API Gatekeeper.
*   **Maintainability:** Modular, OOP design (max 150 lines per file); clear separation of agents, config, and core SDK.

### 5.3 Out of Scope
*   Web or Desktop Graphical User Interface (UI).
*   *Note: CI/CD pipeline automation for test coverage is IN SCOPE and mandatory.*

## 6. External Dependencies
*   **Grphify CLI:** For deterministic AST-based graph extraction.
*   **Obsidian:** As the navigation layer and knowledge vault.
*   **CrewAI:** Multi-agent orchestration framework.
*   **LLM API:** The underlying language model provider (e.g., OpenAI, Gemini, or Anthropic).

## 7. Acceptance Criteria & Definition of Done
*   **Milestone 1 (Docs & Setup):** All PRDs, PLAN.md, and `TODO.md` updated. `.env-example` and config files created without hardcoded secrets.
*   **Milestone 2 (SDK & Infrastructure):** `ApiGatekeeper` queueing requests. `ConfigManager` loads `rate_limits.json` and `setup.json`. Unit tests >85% coverage.
*   **Milestone 3 (Core Agents & Graph):** `graph.json` ingested. `Index-First Retrieval` active. `CodeInspectorAgent` and `GraphAnalystAgent` deployed. 
*   **Milestone 4 (Final Report & Validation):** Confusion matrix produced. Token cost analysis completed. CI/CD test coverage automation running.

## 8. Timeline & Milestones
*   **Day 1 (Phase 0–1):** Repository setup, PRDs, architectural diagrams, initial tasks.
*   **Day 2 (Phase 2):** Core infrastructure, API Gatekeeper, configuration, SDK skeleton.
*   **Day 3 (Phase 3):** Grphify parsing, Community Detection, Agent implementation and orchestration.
*   **Day 4 (Phase 4–5):** OOP design refinement, testing, coverage (>85%), security hygiene validation.
*   **Day 5 (Phase 6–8):** Token efficiency experiment, visualization, confusion matrix, README, and final submission packaging.
