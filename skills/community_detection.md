---
name: community_detection
triggers:
  - detect communities
  - community detection
  - find groups
  - cluster modules
  - group files
  - cohesion analysis
  - responsibility clusters
  - module grouping
  - identify subsystems
boundaries: |
  Requires graph.json loaded. Read-only — does not modify graph or source.
  Token budget: allocated by ContextBudgetManager (20% of total, READ_ONLY).
routing_subgraph: community_map
---

# SKILL: Community Detection

## Purpose

Identify and label communities of related nodes in the graph. Use this skill when you need to understand the **subsystem structure** of the codebase — which files/modules belong together and what collective responsibility they share.

## Pre-conditions

- `Graph` object is available with at least 3 nodes.
- `CommunityDetector.detect()` has been called (communities are already computed).
- Community pages exist in the wiki (`wiki/<label>.md`).

## Execution Procedure

### Step 1 — Load Community Index

Read `index.md` to get the list of all detected communities and their sizes. This is the cheapest operation — index.md is always loaded first.

### Step 2 — Rank Communities by Relevance

For the current query:
1. Score each community by keyword overlap with the query.
2. Select the top 2–3 communities for deeper analysis.
3. Load their wiki pages (`wiki/<label>.md`) only.

### Step 3 — Analyse Cohesion

For each selected community, compute:
```
cohesion_ratio = internal_edges / (internal_edges + external_edges)
```
- **cohesion_ratio ≥ 0.7** → well-bounded subsystem
- **cohesion_ratio 0.4–0.7** → mixed concern, review boundaries
- **cohesion_ratio < 0.4** → boundary probably misdrawn; consider merge/split

### Step 4 — Label Responsibilities

For each community, derive the dominant responsibility from the most common:
- File path prefix (e.g., `services/`, `models/`, `utils/`)
- Node type distribution (if mostly `class` nodes → likely a domain layer)
- Edge pattern (if most edges are EXTRACTED calls → runtime dependency)

### Step 5 — Identify Cross-Community Bridges

Find nodes that appear in edges connecting two different communities:
- These are **bridge nodes** — they mediate between subsystems.
- High-degree bridge nodes with cross-ratio > 60% → flag for `HubVsBottleneckClassifier`.

## Output Format

Return a structured summary:
```
Community: <name>
  Size: N nodes
  Cohesion: X%
  Responsibility: <dominant label>
  Bridge nodes: [node_id, ...]
  Issues: [excessive external coupling | boundary misalignment | ...]
```

## Boundaries

- Do NOT run `CommunityDetector` again — use already-computed communities.
- Do NOT load wiki pages beyond the top-3 selected (budget discipline).
- Do NOT modify community labels in the graph object.
