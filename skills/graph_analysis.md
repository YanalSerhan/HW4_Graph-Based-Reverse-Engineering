---
name: graph_analysis
triggers:
  - analyse architecture
  - architectural analysis
  - graph analysis
  - extract insights
  - five step pipeline
  - observe relate
  - structural analysis
  - module dependencies
  - call graph
boundaries: |
  Requires graph.json to be loaded. Does NOT modify source files.
  Token budget: allocated by ContextBudgetManager (35% of total).
routing_subgraph: community_analysis
---

# SKILL: Graph Analysis

## Purpose

Apply the five-step inference pipeline to extract architectural insights from the loaded graph. Use this skill when you need to understand **why** the codebase is structured the way it is, not just what it contains.

## Pre-conditions

- `graph.json` has been loaded into memory as a `Graph` object.
- Communities have been detected by `CommunityDetector`.
- Index-First Retrieval has assembled the context (index.md + 2–3 community pages).

## Execution Procedure

### Step 1 — Observe

List all structural facts directly visible in the graph:
- Total node count and breakdown by type (module / class / function / variable)
- Total edge count and breakdown by type (EXTRACTED / INFERRED / AMBIGUOUS)
- Number of communities detected
- Top-5 nodes by degree centrality

### Step 2 — Relate

Identify relationships between the observed facts:
- Which communities communicate most (highest inter-community edge count)?
- Are there nodes that bridge two or more communities?
- Do any communities have identical dominant responsibility labels (possible duplication)?

### Step 3 — Confidence

Assign a confidence level to each relationship identified:
- Facts derived from EXTRACTED edges → **HIGH confidence**
- Facts derived from INFERRED edges → **MEDIUM confidence** (send to CodeInspector)
- Facts derived from AMBIGUOUS edges → **LOW confidence** (escalate for human review)

### Step 4 — Context

Place findings in the broader architectural context:
- Which OSI / Clean Architecture layer does each community map to?
- Are there missing layers (e.g., no persistence layer found)?
- How does the hub structure align with the documented PRD requirements?

### Step 5 — Source

For every finding, cite the specific node ID and edge in graph.json:
```
Finding: "Module X acts as a gateway to Layer Y"
Source: node_id="module_x", edges=[("module_x", "layer_y_service", INFERRED)]
```

## Output Format

Return a list of `ArchitecturalInsight` objects with all five fields populated.
Each insight must have at least one `source_node_id` pointing to evidence in the graph.

## Boundaries

- Do NOT read source code files directly — that is the CodeInspector's role.
- Do NOT modify graph.json.
- Do NOT make LLM calls outside the `ApiGatekeeper.execute()` wrapper.
