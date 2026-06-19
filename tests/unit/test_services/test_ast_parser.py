"""
Tests for ASTGraphBuilder and ast_node_processor.
"""

from pathlib import Path

from graph_rev_eng.constants import EDGE_TYPE_AMBIGUOUS, EDGE_TYPE_EXTRACTED
from graph_rev_eng.services.ast_parser import ASTGraphBuilder


def test_simple_valid_python_file(tmp_path: Path):
    """Test that parsing a simple valid Python file with one function produces
    a module and function node."""
    file_path = tmp_path / "simple.py"
    file_path.write_text(
        "def hello():\n    pass\n",
        encoding="utf-8",
    )

    builder = ASTGraphBuilder()
    graph = builder.build(tmp_path)

    # We should have a module node and a function node
    assert len(graph.nodes) == 2
    assert "file:simple.py" in graph.nodes
    assert "func:simple.py:hello" in graph.nodes

    # We should have an edge between module and function
    assert len(graph.edges) == 1
    edge = graph.edges[0]
    assert edge.source_id == "file:simple.py"
    assert edge.target_id == "func:simple.py:hello"
    assert edge.edge_type == EDGE_TYPE_EXTRACTED


def test_function_call_extracted_edge(tmp_path: Path):
    """Test that a function call between two functions produces an EXTRACTED edge."""
    file_path = tmp_path / "calls.py"
    file_path.write_text(
        "def helper():\n    pass\n\ndef main():\n    helper()\n",
        encoding="utf-8",
    )

    builder = ASTGraphBuilder()
    graph = builder.build(tmp_path)

    assert "func:calls.py:helper" in graph.nodes
    assert "func:calls.py:main" in graph.nodes
    assert "call:helper" in graph.nodes

    # There should be an edge from the file to the call node
    call_edges = [e for e in graph.edges if e.target_id == "call:helper"]
    assert len(call_edges) == 1
    assert call_edges[0].source_id == "file:calls.py"
    assert call_edges[0].edge_type == EDGE_TYPE_EXTRACTED


def test_import_statement(tmp_path: Path):
    """Test that an import statement produces a module node and edge."""
    file_path = tmp_path / "imports.py"
    file_path.write_text(
        "import os\nfrom datetime import datetime\n",
        encoding="utf-8",
    )

    builder = ASTGraphBuilder()
    graph = builder.build(tmp_path)

    assert "module:os" in graph.nodes
    assert "module:datetime" in graph.nodes

    os_edges = [e for e in graph.edges if e.target_id == "module:os"]
    assert len(os_edges) == 1
    assert os_edges[0].source_id == "file:imports.py"
    assert os_edges[0].edge_type == EDGE_TYPE_EXTRACTED

    datetime_edges = [e for e in graph.edges if e.target_id == "module:datetime"]
    assert len(datetime_edges) == 1
    assert datetime_edges[0].source_id == "file:imports.py"
    assert datetime_edges[0].edge_type == EDGE_TYPE_EXTRACTED


def test_syntax_error_python2_print(tmp_path: Path):
    """Test that a file with a Python 2 print statement produces an error node
    with AMBIGUOUS edge."""
    file_path = tmp_path / "py2.py"
    file_path.write_text(
        "def bad():\n    print 'Hello Python 2'\n",
        encoding="utf-8",
    )

    builder = ASTGraphBuilder()
    graph = builder.build(tmp_path)

    assert "error:py2.py:syntax" in graph.nodes

    # Check for AMBIGUOUS edge
    ambiguous_edges = [e for e in graph.edges if e.edge_type == EDGE_TYPE_AMBIGUOUS]
    assert len(ambiguous_edges) == 1
    assert ambiguous_edges[0].source_id == "file:py2.py"
    assert ambiguous_edges[0].target_id == "error:py2.py:syntax"


def test_python_builtins_filtered(tmp_path: Path):
    """Test that Python builtins (print, input, int) are filtered out and NOT added as nodes."""
    file_path = tmp_path / "builtins.py"
    file_path.write_text(
        "def my_func():\n    x = input('Prompt')\n    y = int(x)\n    print(y)\n",
        encoding="utf-8",
    )

    builder = ASTGraphBuilder()
    graph = builder.build(tmp_path)

    assert "func:builtins.py:my_func" in graph.nodes
    assert "call:print" not in graph.nodes
    assert "call:input" not in graph.nodes
    assert "call:int" not in graph.nodes


def test_empty_directory(tmp_path: Path):
    """Test that an empty directory produces an empty graph."""
    builder = ASTGraphBuilder()
    graph = builder.build(tmp_path)

    assert len(graph.nodes) == 0
    assert len(graph.edges) == 0
