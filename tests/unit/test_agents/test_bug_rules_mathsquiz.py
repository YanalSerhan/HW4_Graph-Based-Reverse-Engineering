from graph_rev_eng.services.agents.bug_rules_mathsquiz import detect_mathsquiz_logic_bugs
from graph_rev_eng.services.graph_models import Graph, GraphNode


def test_detect_mathsquiz_logic_bugs(tmp_path):
    maths_file = tmp_path / "mathsquiz.py"

    content = """
if answer = 55:
    pass
print("Question 1:")
print("Question 1:")
# 8 x 7 should be 55
# 4 x 9 should be 49
else if answer == 36:
    pass
"""
    maths_file.write_text(content, encoding="utf-8")

    graph = Graph()
    node = GraphNode(
        node_id="n1", node_type="module", label="mathsquiz.py", file_path=str(maths_file)
    )
    graph.nodes["n1"] = node

    bugs = detect_mathsquiz_logic_bugs(graph)

    bug_types = [b.bug_type for b in bugs]
    assert "LOGIC_ERROR" in bug_types
    assert "COPY_PASTE_ERROR" in bug_types
    assert "SYNTAX_ERROR" in bug_types

def test_detect_mathsquiz_no_target_file():
    graph = Graph()
    bugs = detect_mathsquiz_logic_bugs(graph)
    assert len(bugs) == 0
