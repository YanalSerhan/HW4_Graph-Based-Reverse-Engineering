# Mechanism PRD: Skill Routing

## 1. Theoretical Background
AI agents perform best when provided with narrow, task-specific instructions (Skills) rather than massive, generalized prompts. In a graph-based reverse engineering system, an agent must be able to invoke specific analysis techniques (e.g., "detect god-nodes", "trace inheritance") dynamically. The `SKILL.md` infrastructure encapsulates these instructions in markdown files, making them readable by both humans and agents, and routable via semantic matching.

## 2. SKILL.md Anatomy
Each skill is defined as a standalone `.md` file containing two parts:

### 2.1 YAML Frontmatter
Used by the `SkillRouter` for discovery and safety checks without loading the entire file:
*   `name`: The identifier of the skill.
*   `triggers`: A list of natural language phrases (e.g., ["find bottlenecks", "god node"]).
*   `boundaries`: Scope limitations (e.g., `max_nodes: 50`, `read_only: true`).
*   `routing_subgraph`: A pointer indicating which subset of the graph this skill typically requires.

### 2.2 Markdown Execution Body
A step-by-step procedure the agent must follow. Formatted in standard Markdown, it outlines:
*   **Objective:** What the skill achieves.
*   **Procedure:** Numbered steps for execution.
*   **Validation:** How the agent verifies its findings before returning.

## 3. Skill-to-Need Routing
Given a natural language query, the `SkillRouter` performs a semantic search (using lightweight embeddings or simple TF-IDF matching) against the `triggers` defined in the YAML frontmatter of all available `SKILL.md` files. Once a match is found, only that specific skill's body is loaded into the agent's context.

## 4. Specific I/O Requirements
*   **Input:** Natural language user query.
*   **Output:** The path to the selected `SKILL.md` file and its parsed execution body.

## 5. Constraints
*   **Token Budget:** The loaded skill body must fit within the `skillListingBudgetFraction`.
*   **Fallback:** If no skill matches with sufficient confidence, the router must return a generic `fallback_analysis` skill rather than halting.

## 6. Alternative Approaches Considered
*   **Hardcoded Agent Functions:** Relying on native Python functions bound to the agent. Rejected because it is opaque to the user. `SKILL.md` allows users (via Obsidian) to read, modify, and create new agent skills natively.
*   **Single Massive System Prompt:** Placing all skills in the main prompt. Rejected due to catastrophic token waste and distraction.

## 7. Acceptance & Test Criteria
*   **Criteria 1:** Three base `SKILL.md` files are present in the `skills/` directory with correct YAML syntax.
*   **Criteria 2:** `SkillRouter` can parse the YAML frontmatter independently of the markdown body.
*   **Criteria 3:** Given the query "find communities", the router correctly selects `community_detection.md`.
