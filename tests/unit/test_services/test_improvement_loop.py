from unittest.mock import MagicMock

from graph_rev_eng.services.graph_models import Graph
from graph_rev_eng.services.improvement_loop import run_improvement_loop


def test_run_improvement_loop_no_bugs():
    graph = Graph()
    communities = []
    bugs = []
    errors = []
    repo_path = MagicMock()

    g, c, b = run_improvement_loop(
        graph, communities, bugs, repo_path, errors,
        lambda x: graph, lambda x, y: communities, lambda x, y, z: bugs
    )
    assert b == []

def test_run_improvement_loop_resolves_bugs():
    graph = Graph()
    communities = []
    bugs = [MagicMock()]
    errors = []
    repo_path = MagicMock()

    mock_detect_bugs = MagicMock(side_effect=[[], []])

    g, c, b = run_improvement_loop(
        graph, communities, bugs, repo_path, errors,
        lambda x: graph, lambda x, y: communities, mock_detect_bugs
    )
    assert b == []
