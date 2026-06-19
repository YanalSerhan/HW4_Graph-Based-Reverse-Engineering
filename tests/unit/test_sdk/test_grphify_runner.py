from unittest.mock import MagicMock, patch

from graph_rev_eng.sdk.grphify_runner import run_grphify_cli


def test_run_grphify_cli_success(tmp_path):
    results_dir = tmp_path / "results"

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock()

        output_path, html_path, report_path = run_grphify_cli("dummy_repo", results_dir)

        mock_run.assert_called_once()
        assert output_path == results_dir / "graph.json"
        assert html_path.exists()
        assert report_path.exists()

def test_run_grphify_cli_fallback(tmp_path):
    results_dir = tmp_path / "results"

    with patch("subprocess.run", side_effect=FileNotFoundError), \
         patch("graph_rev_eng.services.ast_parser.ASTGraphBuilder.build") as mock_build:

        mock_graph = MagicMock()
        mock_graph.nodes = {}
        mock_graph.edges = []
        mock_build.return_value = mock_graph

        output_path, html_path, report_path = run_grphify_cli("dummy_repo", results_dir)

        assert mock_build.call_count >= 1
        assert output_path.exists()
        assert html_path.exists()
        assert report_path.exists()
