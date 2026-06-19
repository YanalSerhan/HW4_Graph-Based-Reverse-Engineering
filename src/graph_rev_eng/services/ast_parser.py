"""
Python AST Parser — fallback for when Grphify CLI is not available.

Scans a given repository path for .py files, parses them with the `ast` module,
and constructs a Graph containing file/function nodes and import/call edges.
"""

import ast
import logging
from pathlib import Path

from .ast_node_processor import process_ast_tree
from .graph_models import Graph, GraphEdge, GraphNode

logger = logging.getLogger(__name__)


class ASTGraphBuilder:
    """
    Builds a Graph object from a repository directory using Python AST parsing.
    """

    def build(self, repo_path: Path) -> Graph:
        graph = Graph()
        py_files = list(repo_path.glob("**/*.py"))

        logger.info("AST Parser: Found %d Python files in %s", len(py_files), repo_path)

        for py_file in py_files:
            if py_file.name.endswith("_fixed.py"):
                continue
            try:
                rel_path = py_file.relative_to(repo_path).as_posix()
            except ValueError:
                rel_path = py_file.name

            # Create node for file (module)
            file_node_id = f"file:{rel_path}"
            graph.nodes[file_node_id] = GraphNode(
                node_id=file_node_id,
                label=py_file.name,
                node_type="module",
                file_path=rel_path,
            )

            try:
                source = py_file.read_text(encoding="utf-8", errors="replace")
                tree = ast.parse(source)
                process_ast_tree(tree, file_node_id, rel_path, graph)
            except SyntaxError as e:
                logger.warning("AST Parse error in %s: %s", py_file, e)
                error_node_id = f"error:{rel_path}:syntax"
                graph.nodes[error_node_id] = GraphNode(
                    node_id=error_node_id,
                    label=f"SyntaxError: {str(e)}",
                    node_type="error",
                    file_path=rel_path,
                )
                from ..constants import EDGE_TYPE_AMBIGUOUS

                graph.edges.append(
                    GraphEdge(
                        source_id=file_node_id,
                        target_id=error_node_id,
                        edge_type=EDGE_TYPE_AMBIGUOUS,
                        confidence=0.4,
                        label="has_error",
                    )
                )

        return graph


