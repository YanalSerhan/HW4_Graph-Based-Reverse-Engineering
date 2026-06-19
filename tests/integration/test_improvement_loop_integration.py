from graph_rev_eng.services.agents.bug_types import ArchitecturalBug
from graph_rev_eng.services.graph_models import Graph
from graph_rev_eng.services.improvement_loop import run_improvement_loop


def test_improvement_loop():
    graph = Graph()
    communities = []

    bug = ArchitecturalBug(
        bug_type="SPOF",
        severity="HIGH",
        description="A bug",
        affected_node_ids=[],
        recommendation="Do nothing",
    )

    def load_graph(errs):
        return graph

    def detect_comm(g, errs):
        return communities

    def detect_bugs(g, c, errs):
        return []

    new_g, new_c, new_b = run_improvement_loop(
        graph,
        communities,
        [bug],
        "repo",
        [],
        load_graph_cb=load_graph,
        detect_communities_cb=detect_comm,
        detect_bugs_cb=detect_bugs
    )

    assert len(new_b) == 0
