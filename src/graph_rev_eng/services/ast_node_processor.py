"""
ast_node_processor.py — AST node extraction logic for ASTGraphBuilder.
"""
import ast

from ..constants import EDGE_TYPE_EXTRACTED
from .graph_models import Graph, GraphEdge, GraphNode


def process_ast_tree(tree: ast.AST, file_node_id: str, file_path: str, graph: Graph) -> None:
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
            graph.edges.append(
                GraphEdge(
                    source_id=file_node_id,
                    target_id=func_id,
                    edge_type=EDGE_TYPE_EXTRACTED,
                    label="contains",
                )
            )

        elif isinstance(node, ast.ClassDef):
            class_id = f"class:{file_path}:{node.name}"
            graph.nodes[class_id] = GraphNode(
                node_id=class_id,
                label=node.name,
                node_type="class",
                file_path=file_path,
                line_number=node.lineno,
            )
            graph.edges.append(
                GraphEdge(
                    source_id=file_node_id,
                    target_id=class_id,
                    edge_type=EDGE_TYPE_EXTRACTED,
                    label="contains",
                )
            )

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
                graph.edges.append(
                    GraphEdge(
                        source_id=file_node_id,
                        target_id=target_id,
                        edge_type=EDGE_TYPE_EXTRACTED,
                        label="calls",
                    )
                )

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
                graph.edges.append(
                    GraphEdge(
                        source_id=file_node_id,
                        target_id=target_id,
                        edge_type=EDGE_TYPE_EXTRACTED,
                        label="imports",
                    )
                )

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
                graph.edges.append(
                    GraphEdge(
                        source_id=file_node_id,
                        target_id=target_id,
                        edge_type=EDGE_TYPE_EXTRACTED,
                        label="imports",
                    )
                )
