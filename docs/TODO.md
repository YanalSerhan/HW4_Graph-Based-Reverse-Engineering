# TODO.md — EX04: Reverse Engineering of Graph Knowledge Systems
### AI Agent Architecture with Grphify + Obsidian
> **Dr. Yoram Segal | Lecture 07 | June 2026**
> Cross-referenced with `software_submission_guidelines-V3.pdf`

---

> **How to use this checklist:** Work top-to-bottom within each phase. Never begin a phase without completing all mandatory gates from the previous one. Every `- [ ]` maps to a concrete, verifiable requirement from either the submission guidelines or the lesson assignment. The "Path to Excellence" section at the bottom is your ticket to a legendary grade.

---

## Phase 0 — Repository Bootstrap & Mandatory Structure

> **Gate:** Nothing else begins until this phase is 100% green.
> **Definition of Done:** All functional and non-functional requirements in this phase must be fully verified.

- [x] [P1] [Done] [Owner: AI Agent] Create a new Git repository with a meaningful name (e.g., `ex04-graph-reverse-engineering`)
- [x] [P1] [Done] [Owner: AI Agent] Initialize with a proper `.gitignore` covering `.env`, `*.key`, `*.pem`, `credentials.json`, `__pycache__`, `.venv`, `uv.lock` (local), and IDE files
- [x] [P1] [Done] [Owner: AI Agent] Commit an initial `README.md` placeholder at the repo root (will be expanded in Phase 2)
- [x] [P1] [Done] [Owner: AI Agent] Create the full mandatory directory skeleton:
  ```
  project-root/
  ├── src/<your_package>/
  │   ├── __init__.py
  │   ├── sdk/sdk.py
  │   ├── services/
  │   ├── shared/
  │   │   ├── gatekeeper.py
  │   │   ├── config.py
  │   │   └── version.py
  │   └── constants.py
  ├── tests/unit/ & tests/integration/ & tests/conftest.py
  ├── docs/
  ├── config/setup.json & config/rate_limits.json & config/logging_config.json
  ├── data/
  ├── results/
  ├── assets/
  ├── notebooks/
  ├── pyproject.toml
  ├── .env-example
  └── .gitignore
  ```
- [x] [P1] [Done] [Owner: AI Agent] Initialize `uv` as the **sole** package manager — run `uv init` and confirm `pyproject.toml` is generated; **never use** `pip install`, `python -m venv`, or `pip freeze` anywhere
- [x] [P1] [Done] [Owner: AI Agent] Set initial version to `1.00` in `src/<package>/shared/version.py`
- [x] [P1] [Done] [Owner: AI Agent] Set version `1.00` under the `"version"` key in `config/setup.json`
- [x] [P1] [Done] [Owner: AI Agent] Set version `1.00` under `"rate_limits.version"` in `config/rate_limits.json`
- [x] [P1] [Done] [Owner: AI Agent] Create `.env-example` with all required secret placeholder keys (e.g., `LLM_API_KEY=`, `GRPHIFY_TOKEN=`) — **no real values**
- [x] [P1] [Done] [Owner: AI Agent] Confirm `.env` is git-ignored and never committed
- [x] [P1] [Done] [Owner: AI Agent] Create `pyproject.toml` with package name, version `1.00`, author, description, and pinned dependencies (all with explicit version ranges)
- [x] [P1] [Done] [Owner: AI Agent] Run `uv lock` to generate `uv.lock` and commit it

---

## Phase 1 — Documentation & Planning (Must Be Approved Before Any Code)

> **Gate:** All documents in this phase must be written and self-reviewed before a single line of implementation code is written. This is a hard requirement from the guidelines.
> **Definition of Done:** All functional and non-functional requirements in this phase must be fully verified.

### 1.1 — Product Requirements Document (`docs/PRD.md`)

- [x] [P1] [Done] [Owner: AI Agent] Write project overview: describe the reverse engineering problem — understanding an unfamiliar Python codebase using AI agents, Grphify, and Obsidian
- [x] [P1] [Done] [Owner: AI Agent] Define the target user and the pain point (context-window bottleneck; "Lost in the Middle" problem for LLMs analyzing large codebases)
- [x] [P1] [Done] [Owner: AI Agent] Specify the chosen GitHub repository for reverse engineering (must be a real, non-trivial Python repo — e.g., `BugsInPy` or a similarly meaningful codebase; document the rationale for the choice)
- [x] [P1] [Done] [Owner: AI Agent] Define measurable goals (KPIs): e.g., % of token reduction vs. naive RAG baseline, number of architectural insights extracted, Confusion Matrix metrics for agent accuracy
- [x] [P1] [Done] [Owner: AI Agent] List functional requirements: graph generation, community detection, hub/bottleneck identification, PRD-to-implementation traceability, agent-driven bug/smell detection
- [x] [P1] [Done] [Owner: AI Agent] List non-functional requirements: performance (token efficiency), security (no hardcoded secrets), reliability (deterministic AST extraction), maintainability (modular agents)
- [x] [P1] [Done] [Owner: AI Agent] List explicit out-of-scope items (e.g., UI front-end). Note: CI/CD pipeline automation for test coverage is mandatory.
- [x] [P1] [Done] [Owner: AI Agent] Define external dependencies: Grphify CLI, Obsidian, CrewAI or LangGraph, chosen LLM API
- [x] [P1] [Done] [Owner: AI Agent] Write acceptance criteria and definition of done for each major deliverable
- [x] [P1] [Done] [Owner: AI Agent] Define a timeline with milestones (e.g., Phase 0–1: Day 1, Phase 2–3: Day 2–3, Phase 4–5: Day 4–5)

### 1.2 — Algorithm/Mechanism PRDs (`docs/PRD_<mechanism>.md`)

- [x] [P1] [Done] [Owner: AI Agent] `docs/PRD_graph_extraction.md` — Grphify AST parsing: describe Extracted vs. Inferred vs. Ambiguous edge types, confidence levels, and validation rules
- [x] [P1] [Done] [Owner: AI Agent] `docs/PRD_agent_orchestration.md` — CrewAI or LangGraph multi-agent design: roles (Graph Analyst, Code Inspector, GitHub Downloader, Report Writer), inter-agent communication, and termination conditions
- [x] [P1] [Done] [Owner: AI Agent] `docs/PRD_context_management.md` — Context budgeting strategy: Index-First Retrieval (`index.md` → 2–3 targeted pages), `/compact` protocol, position-aware context allocation to defeat "Lost in the Middle"
- [x] [P1] [Done] [Owner: AI Agent] `docs/PRD_skill_routing.md` — SKILL.md anatomy and Skill-to-Need routing: YAML frontmatter (triggers, boundaries), Markdown execution body, semantic subgraph selection
- [x] [P1] [Done] [Owner: AI Agent] `docs/PRD_token_cost_analysis.md` — Token counting methodology: before/after Grphify, measurement protocol, cost breakdown table (model, input tokens, output tokens, total cost)

Each PRD above must include: theoretical background, specific I/O requirements, constraints, alternative approaches considered, and acceptance/test criteria.

### 1.3 — Architecture & Planning Document (`docs/PLAN.md`)

- [x] [P1] [Done] [Owner: AI Agent] Draw a C4 Context diagram: show the system (your AI agent pipeline) in relation to the GitHub repo, Grphify CLI, Obsidian Vault, and the LLM API
- [x] [P1] [Done] [Owner: AI Agent] Draw a C4 Container diagram: Grphify (compute engine), Obsidian (navigation layer), Agent Orchestrator, SDK layer, and API Gatekeeper
- [x] [P1] [Done] [Owner: AI Agent] Draw a C4 Component diagram for the agent orchestrator: individual agents, their responsibilities, and data flows
- [x] [P1] [Done] [Owner: AI Agent] Include a UML sequence diagram for the main workflow: Clone → Grphify scan → `graph.json` → `index.md` → Agent reads index → Agent fetches targeted subgraph → Agent produces insight → Report
- [x] [P1] [Done] [Owner: AI Agent] Document the three-layer architecture (Raw Files → Grphify → Obsidian) with rationale
- [x] [P1] [Done] [Owner: AI Agent] Document key Architectural Decision Records (ADRs): why CrewAI vs. LangGraph was chosen, why Grphify over naive RAG, why Index-First Retrieval over full-context loading
- [x] [P1] [Done] [Owner: AI Agent] Include a data flow diagram showing `graph.json` → `hot.md` → `index.md` → targeted skill pages → agent context
- [x] [P1] [Done] [Owner: AI Agent] Document the API gatekeeper interface (class signature, rate-limit config structure)

### 1.4 — Task Tracking Document (`docs/TODO.md`)

- [x] [P1] [Done] [Owner: AI Agent] **This file you are reading** — keep it updated throughout the project
- [x] [P1] [Done] [Owner: AI Agent] Assign priority and status (Not Started / In Progress / Done) to every task
- [x] [P1] [Done] [Owner: AI Agent] Assign owner (yourself or a named AI agent persona) to each task
- [x] [P1] [Done] [Owner: AI Agent] Define "Definition of Done" for each phase gate

---

## Phase 2 — Core Infrastructure & SDK Layer

> **Gate:** All Phase 1 documents approved. No business logic before the SDK scaffold exists.
> **Definition of Done:** All functional and non-functional requirements in this phase must be fully verified.

### 2.1 — Package & Version Infrastructure

- [x] [P1] [Done] [Owner: AI Agent] Implement `src/<package>/shared/version.py`: expose `__version__ = "1.00"` and a `check_config_version(config: dict)` function that validates config version matches at startup
- [x] [P1] [Done] [Owner: AI Agent] Implement `src/<package>/constants.py`: define all immutable constants (edge type labels `EXTRACTED`, `INFERRED`, `AMBIGUOUS`; confidence thresholds; max file lines guard; default token budget)
- [x] [P1] [Done] [Owner: AI Agent] Implement `src/<package>/__init__.py`: export public API via `__all__`, expose `__version__`
- [x] [P1] [Done] [Owner: AI Agent] Confirm all file sizes are ≤ 150 lines of code (comments and blank lines excluded); split immediately if approaching limit

### 2.2 — Configuration Manager

- [x] [P1] [Done] [Owner: AI Agent] Implement `src/<package>/shared/config.py`: load `config/setup.json` at startup, validate version, expose typed getters — **zero hardcoded values anywhere else in the codebase**
- [x] [P1] [Done] [Owner: AI Agent] Implement `config/rate_limits.json` with the required structure:
  ```json
  { "rate_limits": { "version": "1.00", "services": { "default": {
      "requests_per_minute": 30, "requests_per_hour": 500,
      "concurrent_max": 5, "retry_after_seconds": 30, "max_retries": 3
  }}}}
  ```
- [x] [P1] [Done] [Owner: AI Agent] Implement `config/logging_config.json` — structured JSON logging config
- [x] [P1] [Done] [Owner: AI Agent] All API keys and secrets accessed exclusively via `os.environ.get("KEY_NAME")` — never as string literals

### 2.3 — API Gatekeeper (`src/<package>/shared/gatekeeper.py`)

- [x] [P1] [Done] [Owner: AI Agent] Implement `ApiGatekeeper` class with `__init__(self, config: RateLimitConfig)`, `execute(self, api_call, *args, **kwargs)`, and `get_queue_status(self) -> QueueStatus`
- [x] [P1] [Done] [Owner: AI Agent] Enforce rate limits (per-minute and per-hour) before every LLM API call — queue requests if limit is reached
- [x] [P1] [Done] [Owner: AI Agent] Implement FIFO queue with configurable max depth; trigger backpressure signal when full
- [x] [P1] [Done] [Owner: AI Agent] Implement retry logic with exponential backoff for transient failures, using `max_retries` from config
- [x] [P1] [Done] [Owner: AI Agent] Log every API call (timestamp, model, input token count, output token count, cost estimate, success/failure)
- [x] [P1] [Done] [Owner: AI Agent] Confirm **zero** direct LLM API calls exist anywhere outside this gatekeeper

### 2.4 — SDK Layer (`src/<package>/sdk/sdk.py`)

- [x] [P1] [Done] [Owner: AI Agent] Implement `ReverseEngineeringSDK` as the single entry point for all business logic
- [x] [P1] [Done] [Owner: AI Agent] Expose methods: `run_grphify(repo_path: str) -> Path`, `load_graph(graph_path: Path) -> Graph`, `build_index(graph: Graph) -> Index`, `route_skill(query: str, graph: Graph) -> Skill`, `run_agents(task: str) -> Report`
- [x] [P1] [Done] [Owner: AI Agent] Verify that no GUI, CLI, or external caller ever accesses business logic except through this SDK class
- [x] [P1] [Done] [Owner: AI Agent] Write a `src/main.py` that wires CLI arguments → SDK → output, with no business logic of its own

---

## Phase 3 — Core AI Agent Implementation

> This is the heart of EX04. Every sub-task here maps to the lesson's core assignment requirements.

### 3.1 — Repository Cloning & Environment Setup Agent

- [x] [P1] [Done] [Owner: AI Agent] Implement a `GitHubDownloaderAgent` (as a CrewAI `Agent` or LangGraph `node`) that: accepts a GitHub URL, clones the target repo (e.g., `BugsInPy`) into `data/`, and handles environment setup for the chosen codebase
- [x] [P1] [Done] [Owner: AI Agent] If using `BugsInPy`, implement the virtual environment setup logic per its README — document any friction in the Prompt Engineering Log
- [x] [P1] [Done] [Owner: AI Agent] Validate the clone is clean and the target Python files are accessible before proceeding
- [x] [P1] [Done] [Owner: AI Agent] Write unit tests for the cloning logic with a mock repo

### 3.2 — Grphify Graph Generation

- [x] [P1] [Done] [Owner: AI Agent] Run `grphify` CLI on the cloned codebase and generate `graph.json` — save to `results/`
- [x] [P1] [Done] [Owner: AI Agent] Generate and save `results/GRAPH_REPORT.md` — the Grphify narrative report summarizing architectural findings, anomalies, and community descriptions
- [x] [P1] [Done] [Owner: AI Agent] Parse `graph.json` and build an in-memory `Graph` object with typed nodes and edges
- [x] [P1] [Done] [Owner: AI Agent] Implement `GraphLoader` service that validates all three edge types (`Extracted`, `Inferred`, `Ambiguous`) are correctly parsed
- [x] [P1] [Done] [Owner: AI Agent] Parse, validate, and handle `Hyperedge` (group connections) in the graph, ensuring all members of the group are checked together when drawing conclusions
- [x] [P1] [Done] [Owner: AI Agent] Generate `hot.md` (most connected nodes / hubs) and `index.md` (compact entry point for agents) from the graph — these are the primary navigation artifacts
- [x] [P1] [Done] [Owner: AI Agent] Generate and maintain the full LLM Wiki four-layer anatomy: `/raw`, `/wiki`, `index.md`, and `log.md` (the traceability log of knowledge ingestion)
- [x] [P1] [Done] [Owner: AI Agent] Implement a `CommunityDetector` service: identify communities of files using edge density analysis; label each community with its dominant responsibility
- [x] [P1] [Done] [Owner: AI Agent] Implement a `HubVsBottleneckClassifier`: distinguish healthy hubs (clear boundaries, shared abstraction) from risky god-nodes (Single Point of Failure, excessive cross-community dependencies)
- [x] [P1] [Done] [Owner: AI Agent] Write Obsidian-compatible Wikilinks in generated `.md` files so the Vault is navigable

### 3.3 — Index-First Retrieval & Context Budget Manager

- [x] [P1] [Done] [Owner: AI Agent] Implement `ContextBudgetManager`: given a query, (1) load `index.md` first, (2) select only 2–3 most relevant subgraph pages based on semantic matching, (3) assemble a position-aware context (critical rules at edges, supporting detail in middle)
- [x] [P1] [Done] [Owner: AI Agent] Implement the `/compact` protocol: mid-session summarization that resets conversational noise while preserving intent, decisions, and rules at prompt edges
- [x] [P1] [Done] [Owner: AI Agent] Enforce a hard token budget per agent invocation — log every agent call's actual token consumption vs. budget
- [x] [P1] [Done] [Owner: AI Agent] Distinguish and detect `Context Rot` (gradual quality decay) vs. `Overflow` (hard limit exceeded) as separate failure modes within `ContextBudgetManager`
- [x] [P1] [Done] [Owner: AI Agent] Implement `skillListingBudgetFraction` to allocate a specific fraction of the context window exclusively for presenting available SKILLs
- [x] [P1] [Done] [Owner: AI Agent] Implement `Dropping Skill` fallback logic: gracefully omit specific skills from the agent's view when the context budget overflows
- [x] [P1] [Done] [Owner: AI Agent] Implement `TokenCounter` utility: count input and output tokens for every LLM call; accumulate totals for cost analysis

### 3.4 — Architectural Analysis Agents

- [x] [P1] [Done] [Owner: AI Agent] Implement `GraphAnalystAgent`: reads the graph, applies the five-step inference pipeline (Observe → Relate → Confidence → Context → Source), and extracts architectural insights
- [x] [P1] [Done] [Owner: AI Agent] Implement the three-source reading protocol in `GraphAnalystAgent`: load `graph.html` metadata, `GRAPH_REPORT.md` narrative, and `graph.json` evidence before drawing any architectural conclusion
- [x] [P1] [Done] [Owner: AI Agent] Implement `CodeInspectorAgent`: validates graph-inferred insights against the actual source code; marks `Inferred` edges as confirmed or disputed; flags `Ambiguous` edges for human review
- [x] [P1] [Done] [Owner: AI Agent] Implement `SemanticDuplicateValidator` in `CodeInspectorAgent`: before flagging `semantically_similar_to` nodes as duplicates, verify call sites, consumers, tests, and purpose — never recommend merge based on semantic similarity alone
- [x] [P1] [Done] [Owner: AI Agent] Implement `ArchitecturalBugDetector`: identify structural anti-patterns — Single Points of Failure, god-nodes, missing bridges, communities with excessive external connections
- [x] [P1] [Done] [Owner: AI Agent] Map graph communities to OOP class hierarchies — check that `Extracted` call-graph edges align with the repository's class structure
- [x] [P1] [Done] [Owner: AI Agent] Implement PRD-to-implementation traceability check: verify that nodes representing documented requirements (`WHY`, `TODO`, `NOTE` annotations) are connected to their implementation nodes

### 3.5 — Multi-Agent Orchestration

- [x] [P1] [Done] [Owner: AI Agent] Define agent roles and task assignments in a `crew.py` or LangGraph `graph.py`: GitHubDownloader → GraphAnalyst → CodeInspector → BugDetector → ReportWriter
- [x] [P1] [Done] [Owner: AI Agent] Implement agent safety guardrails:
  - Read-only actions (graph traversal, index loading): autonomous
  - Reversible actions (file writes, note creation): conditional — log before executing
  - Irreversible actions (repo modification, external API calls beyond read): require explicit confirmation flag
  - `model-invocation-disable`: prevent the agent from autonomously invoking specific high-risk skills, keeping them under manual/process control
- [x] [P1] [Done] [Owner: AI Agent] Ensure no single agent exceeds the token budget — implement per-agent budget allocation
- [x] [P1] [Done] [Owner: AI Agent] Implement improvement loop in orchestration: after BugDetector recommends a fix, apply it, re-run Grphify, compare new `graph.json` against previous, run unit tests, and verify the anti-pattern is resolved before stopping
- [x] [P1] [Done] [Owner: AI Agent] Implement `ReportWriterAgent`: synthesize all agent outputs into a structured markdown report saved to `results/final_report.md`

### 3.6 — SKILL.md Infrastructure

- [x] [P1] [Done] [Owner: AI Agent] Create at least 3 SKILL.md files (e.g., `skills/graph_analysis.md`, `skills/community_detection.md`, `skills/bug_detection.md`)
- [x] [P1] [Done] [Owner: AI Agent] Each SKILL.md must have: YAML frontmatter (name, triggers list, boundaries, routing_subgraph pointer) and a Markdown execution body (step-by-step procedure)
- [x] [P1] [Done] [Owner: AI Agent] Implement `SkillRouter`: given a natural language query, use semantic search over trigger phrases to select the correct SKILL.md subgraph without loading the entire graph
- [x] [P1] [Done] [Owner: AI Agent] Verify that skill loading never exceeds the allocated token budget for a single invocation


---

## Phase 4 — OOP Design, Code Quality & Testing

### 4.1 — Object-Oriented Design Compliance

- [x] [P1] [Done] [Owner: AI Agent] Audit every class — ensure each has a single responsibility
- [x] [P1] [Done] [Owner: AI Agent] Implement the Modular "Building Blocks" Design paradigm: strictly separate `Data Input`, `Data Output`, and `Data Setup` for core components
- [x] [P1] [Done] [Owner: AI Agent] Implement parallel processing (e.g., Multithreading for I/O-bound tasks, Multiprocessing for CPU-bound tasks) where appropriate for performance efficiency
- [x] [P1] [Done] [Owner: AI Agent] Ensure thread-safety for all concurrent operations (e.g., using locks/queues for shared state)
- [x] [P1] [Done] [Owner: AI Agent] Extract any duplicated logic (same function body in ≥ 2 files) into a shared base class or `Mixin`
- [x] [P1] [Done] [Owner: AI Agent] Ensure every `Mixin` addresses exactly one concern, does not call methods of another Mixin, and is independently testable
- [x] [P1] [Done] [Owner: AI Agent] Use the Template Method pattern for all agent execution flows that share structure but differ in steps
- [x] [P1] [Done] [Owner: AI Agent] No business logic in `main.py`, CLI layer, or GUI layer — all logic lives in `services/` accessed via `sdk.py`
- [x] [P1] [Done] [Owner: AI Agent] Apply the DRY principle: no duplicated `try/except` patterns — create a shared `safe_execute()` wrapper if needed

### 4.2 — Code Style & Linting

- [x] [P1] [Done] [Owner: AI Agent] Configure `ruff` in `pyproject.toml` with required rule sets: `E`, `F`, `W`, `I`, `N`, `UP`, `B`, `C4`, `SIM`; `line-length = 100`; `target-version = "py310"`
- [x] [P1] [Done] [Owner: AI Agent] Run `ruff check .` — confirm **zero** errors or warnings
- [x] [P1] [Done] [Owner: AI Agent] Confirm all files are ≤ 150 lines of code (split any that exceed this)
- [x] [P1] [Done] [Owner: AI Agent] Every public function, class, and module has a `docstring` explaining **why** (rationale), not just what
- [x] [P1] [Done] [Owner: AI Agent] All variable and function names are descriptive and unambiguous — no single-letter variables except in comprehensions
- [x] [P1] [Done] [Owner: AI Agent] Consistent naming style enforced throughout (snake_case for functions/vars, PascalCase for classes)

### 4.3 — Test-Driven Development

- [x] [P1] [Done] [Owner: AI Agent] Follow Red → Green → Refactor for every new function: write the failing test first, implement, then refactor
- [x] [P1] [Done] [Owner: AI Agent] `tests/` directory mirrors `src/` structure: `tests/unit/test_<module>/test_<file>.py`
- [x] [P1] [Done] [Owner: AI Agent] Every public method has at least one unit test covering the happy path and at least one edge/error case
- [x] [P1] [Done] [Owner: AI Agent] All `conftest.py` shared fixtures are in place (mock graph, mock LLM response, mock repo path)
- [x] [P1] [Done] [Owner: AI Agent] All external dependencies (LLM API, file system, GitHub clone) are mocked in unit tests — no tests make real network calls
- [x] [P1] [Done] [Owner: AI Agent] Test files themselves are ≤ 150 lines — split into multiple files if needed
- [x] [P1] [Done] [Owner: AI Agent] Run `uv run pytest tests/` — all tests pass

### 4.4 — Coverage & Quality Gates

- [x] [P1] [Done] [Owner: AI Agent] Configure coverage in `pyproject.toml`:
  ```toml
  [tool.coverage.run]
  source = ["src"]
  omit = ["src/main.py", "*/tests/*"]
  [tool.coverage.report]
  fail_under = 85
  ```
- [x] [P1] [Done] [Owner: AI Agent] Run `uv run pytest --cov=src --cov-report=term-missing` — confirm ≥ 85% coverage
- [x] [P1] [Done] [Owner: AI Agent] Document all edge cases with explicit test cases: empty graph, graph with no communities, Ambiguous-only edge graph, token budget exceeded mid-session
- [ ] [P1] [Not Started] [Owner: AI Agent] Save automated test reports to `results/test_report.html` or `results/coverage_report/`
- [ ] [P1] [Not Started] [Owner: AI Agent] Implement automation in a CI/CD pipeline (`automation in CI/CD pipeline`) to automatically generate and check test coverage reports

---

## Phase 5 — Configuration, Security & Dependency Hygiene

- [x] [P1] [Done] [Owner: AI Agent] Audit every Python file: confirm **zero** hardcoded API keys, tokens, passwords, or URLs that should be configurable
- [x] [P1] [Done] [Owner: AI Agent] Confirm all rate-limit values, timeouts, model names, and API endpoints are read from `config/` files via `ConfigManager`
- [x] [P1] [Done] [Owner: AI Agent] Confirm `.env-example` contains every secret key name with a placeholder value and an explanatory comment
- [x] [P1] [Done] [Owner: AI Agent] Run `git log --all -- '*.env'` — confirm `.env` was never committed
- [x] [P1] [Done] [Owner: AI Agent] Confirm `uv.lock` is present and committed; run `uv sync` on a clean machine to verify reproducibility
- [x] [P1] [Done] [Owner: AI Agent] Confirm `pyproject.toml` specifies all dependencies with version constraints (no bare `dependency = "*"`)
- [x] [P1] [Done] [Owner: AI Agent] Confirm `ruff check .` returns zero errors after all code is written
- [x] [P1] [Done] [Owner: AI Agent] Update `.gitignore` to cover: `.env`, `uv.lock` (if desired to keep out of VCS), `__pycache__`, `*.pyc`, `results/` (large outputs), `data/` (cloned repos)

---

## Phase 6 — Research, Experimentation & Visualization

> This phase is what separates a good project from a great one.

### 6.1 — Token Efficiency Experiment (Mandatory per Assignment)

- [ ] [P1] [Not Started] [Owner: AI Agent] Establish a baseline: run a naive RAG approach (load all skill descriptions into context) on 5 representative queries; record exact token counts (input + output)
- [ ] [P1] [Not Started] [Owner: AI Agent] Run the Grphify graph-based approach on the same 5 queries using Index-First Retrieval; record exact token counts
- [ ] [P1] [Not Started] [Owner: AI Agent] Produce a comparison table in `results/token_analysis.md`:
  | Query | Naive RAG Tokens | Graph-Based Tokens | Reduction % |
  |-------|-----------------|-------------------|-------------|
- [ ] [P1] [Not Started] [Owner: AI Agent] Calculate and report total cost in USD using the cost table format (Model / Input Tokens / Output Tokens / Total Cost)
- [ ] [P1] [Not Started] [Owner: AI Agent] Document token optimization strategies applied: batch processing, context compaction, subgraph pruning

### 6.2 — Parameter Sensitivity Analysis

- [ ] [P1] [Not Started] [Owner: AI Agent] Vary at least 2 parameters (e.g., number of top-k subgraph pages retrieved: 1, 2, 3, 5; confidence threshold for Inferred edges: 0.5, 0.7, 0.9)
- [ ] [P1] [Not Started] [Owner: AI Agent] Run systematic experiments with controlled variation (one parameter at a time — OAT method)
- [ ] [P1] [Not Started] [Owner: AI Agent] Record results in a structured table and compute variance across runs
- [ ] [P1] [Not Started] [Owner: AI Agent] Produce a `notebooks/analysis.ipynb` with all analysis code, plots, and narrative

### 6.3 — Visualization Artifacts (Mandatory)

- [x] [P1] [Done] [Owner: AI Agent] Generate and save `results/graph.json` and `results/graph.html` (interactive graph via Grphify or D3.js/Plotly)
- [ ] [P1] [Not Started] [Owner: AI Agent] Produce a **Community Map** visualization: color-coded communities, hub size proportional to centrality, bridge edges highlighted
- [ ] [P1] [Not Started] [Owner: AI Agent] Produce a **Bar chart**: top 10 nodes by centrality score
- [ ] [P1] [Not Started] [Owner: AI Agent] Produce a **Heatmap**: community-to-community dependency matrix (who depends on whom)
- [ ] [P1] [Not Started] [Owner: AI Agent] Produce a **Token Efficiency Line Chart**: tokens used vs. number of skills loaded (showing the cost of naive approach vs. graph-based)
- [ ] [P1] [Not Started] [Owner: AI Agent] All visualizations: clear labels, accessible colors, high resolution, saved to `assets/`
- [ ] [P1] [Not Started] [Owner: AI Agent] Include at least 2 architecture diagrams (C4 or UML) in `assets/` — referenced in `docs/PLAN.md` and `README.md`

### 6.4 — Confusion Matrix for Agent Accuracy (Bonus from Lecture Q&A)

- [ ] [P1] [Not Started] [Owner: AI Agent] Define a ground-truth dataset: 20–30 architectural facts about the chosen codebase (e.g., "Function X calls Function Y" — True/False)
- [ ] [P1] [Not Started] [Owner: AI Agent] Run the `CodeInspectorAgent` on all items and record its predictions
- [ ] [P1] [Not Started] [Owner: AI Agent] Build a Confusion Matrix: True Positives, False Positives, True Negatives, False Negatives
- [ ] [P1] [Not Started] [Owner: AI Agent] Compute Precision, Recall, F1-score for the agent
- [ ] [P1] [Not Started] [Owner: AI Agent] Save to `results/agent_confusion_matrix.md` and `assets/confusion_matrix.png`

---

## Phase 7 — User Interface & Prompt Engineering Log

### 7.1 — CLI Interface

- [x] [P1] [Done] [Owner: AI Agent] Implement a `src/main.py` CLI using `argparse` or `click` that exposes: `--repo-url`, `--query`, `--budget-tokens`, `--output-dir`, `--compact` (trigger mid-session compaction)
- [ ] [P1] [Not Started] [Owner: AI Agent] Document all CLI flags, their defaults, and example workflows in `README.md`
- [ ] [P1] [Not Started] [Owner: AI Agent] Apply Nielsen's 10 usability heuristics at the CLI level: clear error messages, graceful degradation on failure, confirmation before irreversible actions
- [ ] [P1] [Not Started] [Owner: AI Agent] Save a screenshot (or `asciinema` recording) of a full CLI session to `assets/`

### 7.2 — Prompt Engineering Log (Mandatory per Guidelines)

- [ ] [P1] [Not Started] [Owner: AI Agent] Maintain `docs/prompt_log.md` throughout the project — log every significant prompt used with the LLM during development
- [ ] [P1] [Not Started] [Owner: AI Agent] Each entry must include: objective, full prompt text, sample response, iterative improvements made, and lessons learned
- [ ] [P1] [Not Started] [Owner: AI Agent] Document the prompts used to: generate SKILL.md files, instruct the GraphAnalystAgent, instruct the CodeInspectorAgent, and generate the final report
- [ ] [P1] [Not Started] [Owner: AI Agent] Note which prompting techniques improved results (chain-of-thought, few-shot examples, XML tags for structured output, position-aware placement of rules)

---

## Phase 8 — Final Packaging, Documentation & Submission

### 8.1 — README.md (Comprehensive)

- [ ] [P1] [Not Started] [Owner: AI Agent] **Installation instructions**: system requirements, step-by-step setup using `uv sync`, Grphify CLI installation, Obsidian setup
- [ ] [P1] [Not Started] [Owner: AI Agent] **Usage instructions**: typical workflow with exact CLI commands, flag descriptions, example with `BugsInPy`
- [ ] [P1] [Not Started] [Owner: AI Agent] **Code examples**: 3 concrete usage snippets demonstrating the SDK, a CLI invocation, and a sample agent output
- [ ] [P1] [Not Started] [Owner: AI Agent] **Configuration guide**: explain every key in `config/setup.json` and `config/rate_limits.json`
- [ ] [P1] [Not Started] [Owner: AI Agent] **Contribution guidelines**: code style, test requirements, PR process
- [ ] [P1] [Not Started] [Owner: AI Agent] **License and attribution**: third-party library licenses (Grphify, CrewAI/LangGraph, etc.)
- [ ] [P1] [Not Started] [Owner: AI Agent] Link to `results/graph.html` (interactive visualization) and `results/final_report.md`

### 8.2 — ISO/IEC 25010 Compliance Self-Assessment

- [ ] [P1] [Not Started] [Owner: AI Agent] Complete a self-assessment table in `docs/quality_assessment.md` covering all 8 quality characteristics:
  - Functional Suitability (correctness, completeness, appropriateness)
  - Performance Efficiency (time behavior, resource utilization)
  - Compatibility (interoperability)
  - Usability (learnability, operability, error prevention)
  - Reliability (maturity, fault tolerance, recoverability)
  - Security (confidentiality, integrity, authenticity)
  - Maintainability (modularity, reusability, analyzability, modifiability, testability)
  - Portability (adaptability, installability, replaceability)

### 8.3 — Final Checklist Gate (from Guidelines Section 17)

Run through every item in the submission guidelines' final checklist and mark each as confirmed:

- [ ] [P1] [Not Started] [Owner: AI Agent] **Documentation**: `README.md` at root, `docs/` with `PRD.md`, `PLAN.md`, `TODO.md`, all mechanism PRDs, architecture diagrams, prompt log
- [ ] [P1] [Not Started] [Owner: AI Agent] **Code & Architecture**: SDK layer for all business logic, OOP with no duplication, API Gatekeeper for all LLM calls, rate limits from config, all files ≤ 150 lines, docstrings on all public APIs, consistent naming
- [ ] [P1] [Not Started] [Owner: AI Agent] **Quality & Testing**: TDD workflow followed, ≥ 85% test coverage, `ruff check` zero errors, edge cases documented and tested, automated test reports saved
- [ ] [P1] [Not Started] [Owner: AI Agent] **Security & Config**: separate config files with versioning, `.env-example` present, zero secrets in source code, `.gitignore` updated, `uv` as sole package manager, `uv.lock` and `pyproject.toml` committed
- [ ] [P1] [Not Started] [Owner: AI Agent] **Research & Visualization**: parameter sensitivity analysis, token efficiency experiment with cost table, high-quality visualizations, analysis notebook
- [ ] [P1] [Not Started] [Owner: AI Agent] **Standards & Extensibility**: plugin/extension points documented, package organized as proper Python package, ISO/IEC 25010 self-assessment, references to MIT SQA / Google Engineering / Microsoft API / Nielsen guidelines
- [ ] [P1] [Not Started] [Owner: AI Agent] **General**: clean Git history with meaningful commit messages, license file, deployment instructions

### 8.4 — Git History & Release

- [ ] [P1] [Not Started] [Owner: AI Agent] All commits have meaningful messages following conventional commits format (e.g., `feat:`, `fix:`, `docs:`, `test:`, `refactor:`)
- [ ] [P1] [Not Started] [Owner: AI Agent] Create a Git tag `v1.0.0` for the submission commit
- [ ] [P1] [Not Started] [Owner: AI Agent] All feature branches merged via Pull Requests (even solo work — practice the discipline)
- [ ] [P1] [Not Started] [Owner: AI Agent] Confirm the repo is accessible to the grader

---

## 🚀 Path to Excellence: Uniqueness, Expansions, and Original Thoughts

> These five ideas go far beyond the assignment requirements. They demonstrate genuine mastery of AI agents, graph knowledge architectures, and systems thinking. Implementing even two of them will make this submission unforgettable.

---

### 💡 Idea 1: Live Architectural Drift Detector (CI/CD Integration)

**The Insight:** The lesson mentions that Grphify should be re-run after every significant change. Take this literally and build it into a CI/CD pipeline. Every `git commit` triggers a Grphify rescan, the new `graph.json` is diffed against the previous version, and an `ArchitecturalDriftAgent` reports: "Community X gained 3 new external dependencies since last commit — potential god-node forming."

**Tasks:**
- [ ] [P1] [Not Started] [Owner: AI Agent] Implement `GraphDiffer`: compare two `graph.json` files and produce a structured diff (nodes added/removed, edge type changes, community splits/merges, centrality rank shifts)
- [ ] [P1] [Not Started] [Owner: AI Agent] Create a GitHub Actions workflow (`.github/workflows/arch_check.yml`) that runs Grphify and `GraphDiffer` on every push and posts a summary comment on the PR
- [ ] [P1] [Not Started] [Owner: AI Agent] Implement `DriftAlertAgent`: classify drift as benign (refactor), concerning (new SPOF), or critical (community boundary violation)
- [ ] [P1] [Not Started] [Owner: AI Agent] Visualize drift as a before/after animated graph delta in `results/drift_animation.html`

---

### 💡 Idea 2: Confidence-Weighted Knowledge Graph with Human-in-the-Loop Validation UI

**The Insight:** The three edge types (Extracted, Inferred, Ambiguous) have fundamentally different epistemic statuses. Build a small interactive HTML dashboard that lets a human reviewer quickly validate or reject all `Inferred` and `Ambiguous` edges in batch, turning the graph from a hypothesis into ground truth.

**Tasks:**
- [ ] [P1] [Not Started] [Owner: AI Agent] Build `results/validation_dashboard.html`: a pure HTML/JS/D3.js interface (no backend required) that loads `graph.json` and renders all Inferred/Ambiguous edges as cards with "Confirm ✓ / Reject ✗ / Escalate ?" buttons
- [ ] [P1] [Not Started] [Owner: AI Agent] Implement local state persistence: validation decisions saved to `results/validated_edges.json`
- [ ] [P1] [Not Started] [Owner: AI Agent] Implement `GraphRefiner`: reads `validated_edges.json` and produces a `graph_ground_truth.json` with only confirmed edges — the cleanest possible knowledge graph
- [ ] [P1] [Not Started] [Owner: AI Agent] Feed `graph_ground_truth.json` back into the agent pipeline and measure the Precision/Recall improvement vs. using the raw graph

---

### 💡 Idea 3: Multi-Repository Portfolio Analysis — Org-Level Knowledge Graph

**The Insight:** The lesson introduces the concept of a Portfolio (the top-level collection of projects). Take this to its logical conclusion: instead of reverse engineering one repo, reverse engineer an entire GitHub organization (e.g., 3–5 related repos). Build a cross-repository knowledge graph that reveals shared abstractions, duplicated logic across repos, and missing shared libraries that should be extracted.

**Tasks:**
- [ ] [P1] [Not Started] [Owner: AI Agent] Implement `PortfolioOrchestrator`: accepts a list of GitHub URLs, runs Grphify on each, and merges the resulting graphs using a namespace prefix per repo (`repo_name::module::function`)
- [ ] [P1] [Not Started] [Owner: AI Agent] Implement `CrossRepoDuplicationDetector`: find `semantically_similar_to` edges that span different repositories — these are candidates for a shared library
- [ ] [P1] [Not Started] [Owner: AI Agent] Produce a `results/portfolio_report.md` with executive-level findings: "Functions X, Y, Z appear in 3 repos with 92% similarity — extract to shared utility package"
- [ ] [P1] [Not Started] [Owner: AI Agent] Visualize the multi-repo graph with repo membership as community color

---

### 💡 Idea 4: Automated Dataset Construction for Agent Accuracy Measurement (Full Pipeline)

**The Insight:** The Q&A section of the lecture describes a systematic method for building a ground-truth dataset to measure agent accuracy. Implement the full pipeline described — not just the Confusion Matrix, but the entire data flywheel.

**Tasks:**
- [ ] [P1] [Not Started] [Owner: AI Agent] Implement `DatasetGenerator`: uses an LLM to generate 1,000+ architectural questions about the target codebase (e.g., "Does `function_a` in `module_x` call `function_b` in `module_y`?") with ground-truth answers derived from Grphify's `Extracted` (deterministic) edges
- [ ] [P1] [Not Started] [Owner: AI Agent] Implement `ErrorInjector`: systematically introduce errors into a copy of the codebase (rename functions, change call sites) at increasing rates (5%, 10%, 20%, 50%) to simulate degradation
- [ ] [P1] [Not Started] [Owner: AI Agent] Run the `CodeInspectorAgent` against all error levels and plot the Confusion Matrix at each level — find the "breaking point" where the agent's F1 score collapses
- [ ] [P1] [Not Started] [Owner: AI Agent] Produce a publishable-quality results table and learning curve graph
- [ ] [P1] [Not Started] [Owner: AI Agent] This dataset is a contribution in itself — describe it as a reusable evaluation benchmark for architectural analysis agents

---

### 💡 Idea 5: SKILL.md as a Living, Self-Updating Knowledge Base

**The Insight:** Skills in the lesson are described as static files. Challenge this. What if the `ReportWriterAgent` could identify gaps in the existing SKILL.md library — queries that were poorly answered because no skill covered them — and draft new SKILL.md files automatically, subject to human approval?

**Tasks:**
- [ ] [P1] [Not Started] [Owner: AI Agent] Implement `SkillGapDetector`: after every agent run, log queries where the `SkillRouter` returned low-confidence matches; cluster these into gap categories
- [ ] [P1] [Not Started] [Owner: AI Agent] Implement `SkillDraftAgent`: for each identified gap, generate a candidate `SKILL.md` with correct YAML frontmatter (triggers derived from the gap cluster, boundaries set conservatively) and a Markdown execution body
- [ ] [P1] [Not Started] [Owner: AI Agent] Implement a human approval gate: draft skills are saved to `skills/drafts/` and only promoted to `skills/` after manual review (or a confidence threshold is met)
- [ ] [P1] [Not Started] [Owner: AI Agent] Measure skill library growth over time: track the number of skills, query coverage rate, and average routing confidence across agent sessions
- [ ] [P1] [Not Started] [Owner: AI Agent] Visualize the skill knowledge graph: a meta-graph where nodes are skills and edges represent overlapping trigger domains — reveals redundancy and gaps at a glance

---

## 📋 Quick Reference: Mandatory Compliance Checklist (from Guidelines §19)

| Requirement | Threshold | How to Verify |
|---|---|---|
| SDK architecture | All logic via SDK | `grep -r "import openai" src/` shows only `gatekeeper.py` |
| OOP — no duplication | 0 duplicate function bodies | `ruff check` + manual review |
| API Gatekeeper | All external calls routed | Code review of `gatekeeper.py` |
| Rate limits from config | No hardcoded limits | `grep -r "requests_per" src/` shows only config reads |
| Queue management | No crashes on rate limit | Integration test with mock rate-limit trigger |
| Version tracking | Starts at `1.00` | `version.py`, `setup.json`, `rate_limits.json` |
| File size | ≤ 150 LOC per file | `wc -l src/**/*.py \| sort -n` |
| Linter | 0 errors | `uv run ruff check .` |
| Test coverage | ≥ 85% | `uv run pytest --cov=src` |
| No hardcoded values | 0 secrets/URLs in code | `grep -r "api_key\s*=" src/` |
| No `.env` in Git | Never committed | `git log --all -- .env` returns nothing |
| `uv` only | No pip/venv calls | `grep -r "pip install" .` returns nothing |
| `uv.lock` present | Committed | `ls uv.lock` |

---

*Generated by cross-referencing `L07-Lesson-Summary.pdf` (Parts A, B, C) with `software_submission_guidelines-V3.pdf`. Every task maps to a specific requirement. Build with discipline. Deliver with excellence.*
