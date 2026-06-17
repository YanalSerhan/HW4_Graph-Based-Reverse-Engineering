"""
Python AST Parser — fallback for when Grphify CLI is not available.

Scans a given repository path for .py files, parses them with the `ast` module,
and constructs a Graph containing file/function nodes and import/call edges.
"""

import ast
import logging
from pathlib import Path

from ..constants import EDGE_TYPE_EXTRACTED
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
                self._process_ast_tree(tree, file_node_id, rel_path, graph)
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
                graph.edges.append(GraphEdge(
                    source_id=file_node_id,
                    target_id=error_node_id,
                    edge_type=EDGE_TYPE_AMBIGUOUS,
                    label="has_error"
                ))

        return graph

    def _process_ast_tree(self, tree: ast.AST, file_node_id: str, file_path: str, graph: Graph) -> None:
        """Walks the AST and extracts nodes/edges."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_id = f"func:{file_path}:{node.name}"
                graph.nodes[func_id] = GraphNode(
                    node_id=func_id,
                    label=node.name,
                    node_type="function",
                    file_path=file_path,
                    line_number=node.lineno,
                )
                # Edge: File contains Function
                graph.edges.append(GraphEdge(
                    source_id=file_node_id,
                    target_id=func_id,
                    edge_type=EDGE_TYPE_EXTRACTED,
                    label="contains"
                ))

            elif isinstance(node, ast.ClassDef):
                class_id = f"class:{file_path}:{node.name}"
                graph.nodes[class_id] = GraphNode(
                    node_id=class_id,
                    label=node.name,
                    node_type="class",
                    file_path=file_path,
                    line_number=node.lineno,
                )
                graph.edges.append(GraphEdge(
                    source_id=file_node_id,
                    target_id=class_id,
                    edge_type=EDGE_TYPE_EXTRACTED,
                    label="contains"
                ))

            elif isinstance(node, ast.Call):
                func = node.func
                name = ""
                if isinstance(func, ast.Name):
                    name = func.id
                elif isinstance(func, ast.Attribute):
                    name = func.attr
                
                # Check if it's a builtin
                import builtins
                if name and name not in dir(builtins):
                    target_id = f"call:{name}"
                    if target_id not in graph.nodes:
                        graph.nodes[target_id] = GraphNode(
                            node_id=target_id,
                            label=name,
                            node_type="function",
                            file_path="",
                        )
                    # We assume the file is the source for simplicity
                    graph.edges.append(GraphEdge(
                        source_id=file_node_id,
                        target_id=target_id,
                        edge_type=EDGE_TYPE_EXTRACTED,
                        label="calls"
                    ))

            elif isinstance(node, ast.Import):
                for alias in node.names:
                    target_id = f"module:{alias.name}"
                    if target_id not in graph.nodes:
                        graph.nodes[target_id] = GraphNode(
                            node_id=target_id,
                            label=alias.name,
                            node_type="module",
                            file_path="",
                        )
                    graph.edges.append(GraphEdge(
                        source_id=file_node_id,
                        target_id=target_id,
                        edge_type=EDGE_TYPE_EXTRACTED,
                        label="imports"
                    ))

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    target_id = f"module:{node.module}"
                    if target_id not in graph.nodes:
                        graph.nodes[target_id] = GraphNode(
                            node_id=target_id,
                            label=node.module,
                            node_type="module",
                            file_path="",
                        )
                    graph.edges.append(GraphEdge(
                        source_id=file_node_id,
                        target_id=target_id,
                        edge_type=EDGE_TYPE_EXTRACTED,
                        label="imports"
                    ))
