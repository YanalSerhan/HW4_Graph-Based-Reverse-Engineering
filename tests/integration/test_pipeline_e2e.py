from graph_rev_eng.sdk.sdk import ReverseEngineeringSDK


def test_pipeline_e2e(tmp_path):
    sdk = ReverseEngineeringSDK()

    class MockCloner:
        def clone(self, url):
            return tmp_path / "mock_repo"

    graph_path = tmp_path / "graph.json"
    graph_path.write_text('{"nodes": [], "edges": [], "metadata": {}}', encoding="utf-8")

    def mock_llm_call(prompt):
        return "Mock LLM Response"

    res = sdk.run_agents(
        task="Test",
        github_url="https://github.com/test/test",
        graph_path=graph_path,
        report_path=tmp_path / "report.md",
        cloner=MockCloner()
    )

    assert res.report_path.exists()
    assert res.bug_count >= 0
