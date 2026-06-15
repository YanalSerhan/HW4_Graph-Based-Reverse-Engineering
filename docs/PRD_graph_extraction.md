# Mechanism PRD: Graph Extraction

## 1. Theoretical Background
To reverse-engineer a complex software repository, we must first map its structure. Raw source code is highly unstructured and token-heavy. By leveraging Abstract Syntax Tree (AST) parsing via the Grphify CLI, we can deterministically map a codebase into a property graph, reducing noise and focusing exclusively on architectural connections (function calls, imports, class inheritances).

## 2. Edge Types & Confidence Levels
The generated knowledge graph relies on three distinct epistemic levels of connection:

1.  **Extracted Edges (Confidence: 1.0):**
    *   **Description:** Deterministically extracted relationships directly from the AST (e.g., explicit `import`, direct function calls, inheritance).
    *   **Validation Rule:** Must map exactly to an existing line of code.

2.  **Inferred Edges (Confidence: 0.5 - 0.9):**
    *   **Description:** Relationships deduced by AI agents analyzing patterns, such as likely dependencies or temporal couplings not explicitly defined in code (e.g., passing shared data formats via a database or queue).
    *   **Validation Rule:** Must be validated by the `CodeInspectorAgent` to upgrade its confidence score.

3.  **Ambiguous Edges (Confidence: < 0.5):**
    *   **Description:** Contradictory, unclear, or speculative relationships flagged during community detection or multi-agent conflict.
    *   **Validation Rule:** Must be flagged for human review or removed if validation fails consistently.

## 3. Specific I/O Requirements
*   **Input:** The raw file path of the cloned GitHub repository (e.g., `data/BugsInPy/fastapi`).
*   **Output:** A structured JSON file (`results/graph.json`) representing the Nodes (Files/Functions) and Edges (Relationships).
*   **Intermediate Output:** Markdown visualizations (`hot.md` for hubs, `index.md` for traversal) built on top of the graph.

## 4. Constraints
*   The graph generation must not exceed a reasonable local memory footprint.
*   Hyperedges (group connections) must be handled securely without breaking the traversal logic of downstream agents.
*   Only valid Python files are parsed; non-code assets should be ignored or processed superficially.

## 5. Alternative Approaches Considered
*   **Naive RAG (Vector Search):** Rejected because vector search loses structural context (who calls whom) and treats the codebase as a flat list of text snippets, leading to high token overhead and hallucination.
*   **Regex-based Parsing:** Rejected because it is fragile and cannot resolve complex OOP hierarchies or scope correctly. Grphify's AST approach provides a rigorous structural baseline.

## 6. Acceptance & Test Criteria
*   **Criteria 1:** `Grphify` executes successfully on the target repo and produces a valid `graph.json` without crashing.
*   **Criteria 2:** `GraphLoader` can parse the JSON into an in-memory Graph object without losing edge attributes.
*   **Criteria 3:** Extracted edges have exactly 1.0 confidence.
*   **Criteria 4:** Unit tests verify that cyclic dependencies and isolated nodes do not break the Community Detection service.
