---
name: bug_detection
triggers:
  - detect bugs
  - find anti-patterns
  - architectural issues
  - single point of failure
  - god node
  - spof detection
  - code smell
  - structural risk
  - bottleneck detection
  - excessive coupling
  - traceability gap
boundaries: |
  Read-only graph traversal. Does NOT modify source files.
  Irreversible actions (filing issues, modifying repo): require confirm_irreversible=True.
  Token budget: allocated by ContextBudgetManager (20% of total).
routing_subgraph: bug_detection_map
---

# SKILL: Bug Detection

## Purpose

Identify structural anti-patterns in the codebase graph. Use this skill when you need to find **architectural risks** — problems that transcend individual files and emerge only from the system-level structure.

## Pre-conditions

- `Graph` object available with EXTRACTED, INFERRED, and AMBIGUOUS edges.
- `CommunityDetector` has run (community_id stamped on nodes).
- `HubVsBottleneckClassifier` results available or will be computed here.

## Detection Passes

Run each pass independently. Each pass produces zero or more `ArchitecturalBug` objects.

### Pass 1 — SPOF / God-Node Detection

```
for each node with degree >= 5:
    cross_ratio = cross_community_edges / total_edges
    if cross_ratio > 0.6:
        if degree > 15: classify as GOD_NODE (CRITICAL)
        else: classify as SPOF (HIGH)
```

Recommendation template:
> "Decompose `<node>` into focused sub-modules. Introduce an interface/facade to absorb its coupling."

### Pass 2 — Excessive External Coupling

```
for each community:
    ext_ratio = external_edges / (internal_edges + external_edges)
    if ext_ratio > 0.5: flag as EXCESSIVE_EXTERNAL_COUPLING (MEDIUM)
```

Look for: communities that are effectively utility libraries (used everywhere but
own nothing). These are candidates for extraction into a shared package.

### Pass 3 — OOP Hierarchy Fragmentation

```
for each EXTRACTED edge (source, target):
    if source.file_path == target.file_path:
        if source.community_id != target.community_id:
            flag as OOP_HIERARCHY_FRAGMENTATION (LOW)
```

Symptom: a single file's classes are split across different communities, suggesting
the class hierarchy was structured without regard to the module's responsibility.

### Pass 4 — PRD Traceability Gaps

```
for each node with label containing {WHY, TODO, NOTE, FIXME}:
    if len(graph.neighbors(node_id)) == 0:
        flag as PRD_TRACEABILITY_GAP (MEDIUM)
```

A disconnected annotation node means a documented intent has no implementation link.

## Output Format

For each detected issue, produce:
```
[SEVERITY] BUG_TYPE
  Node(s): <node_ids>
  Description: <what was found>
  Recommendation: <how to fix>
```

## Severity Scale

| Severity | Description |
|----------|-------------|
| CRITICAL | System-level risk — immediate refactor recommended |
| HIGH     | SPOF risk — high blast radius on failure |
| MEDIUM   | Boundary or coupling issue — plan for next sprint |
| LOW      | Style / alignment issue — address in refactor backlog |

## Boundaries

- Do NOT edit source files — output is advisory only.
- Do NOT escalate to CRITICAL without degree > 15 AND cross_ratio > 0.6.
- IRREVERSIBLE actions (opening tickets, modifying repo): require explicit `confirm_irreversible=True`.
