from pathlib import Path
from unittest.mock import MagicMock, patch

from graph_rev_eng.sdk.sdk import ReverseEngineeringSDK
from graph_rev_eng.services.graph_models import Graph


@patch("graph_rev_eng.sdk.sdk.ConfigManager")
@patch("graph_rev_eng.sdk.sdk.TokenCounter")
def test_sdk_init(mock_tc, mock_cm):
    sdk = ReverseEngineeringSDK()
    assert sdk is not None

@patch("graph_rev_eng.sdk.sdk.run_grphify_cli")
def test_sdk_run_grphify(mock_run):
    mock_run.return_value = (Path("a"), Path("b"), Path("c"))
    sdk = ReverseEngineeringSDK()
    res = sdk.run_grphify("repo")
    assert res == (Path("a"), Path("b"), Path("c"))
    mock_run.assert_called_once()

@patch("graph_rev_eng.sdk.sdk.GraphLoader")
def test_sdk_load_graph(mock_gl):
    mock_instance = MagicMock()
    mock_graph = Graph()
    mock_instance.load.return_value = mock_graph
    mock_gl.return_value = mock_instance

    sdk = ReverseEngineeringSDK()
    assert sdk.load_graph(Path("graph.json")) == mock_graph
    mock_instance.load.assert_called_once()

@patch("graph_rev_eng.sdk.sdk.CommunityDetector")
@patch("graph_rev_eng.sdk.sdk.IndexBuilder")
def test_sdk_build_index(mock_ib, mock_cd):
    mock_cd_inst = MagicMock()
    mock_cd_inst.detect.return_value = []
    mock_cd.return_value = mock_cd_inst

    mock_ib_inst = MagicMock()
    mock_ib.return_value = mock_ib_inst

    sdk = ReverseEngineeringSDK()
    res = sdk.build_index(Graph())
    assert isinstance(res, Path)
    mock_cd_inst.detect.assert_called_once()
    mock_ib_inst.build.assert_called_once()

@patch("graph_rev_eng.sdk.sdk.SkillRouter")
def test_sdk_route_skill(mock_sr):
    mock_inst = MagicMock()
    mock_inst.route.return_value = "routed"
    mock_sr.return_value = mock_inst

    sdk = ReverseEngineeringSDK()
    assert sdk.route_skill("query") == "routed"
    mock_inst.route.assert_called_once()

@patch("graph_rev_eng.sdk.sdk.AgentCrew")
@patch("graph_rev_eng.shared.gatekeeper.ApiGatekeeper")
@patch("graph_rev_eng.services.llm.OpenAILLM")
def test_sdk_run_agents(mock_llm, mock_gk, mock_ac):
    mock_inst = MagicMock()
    mock_inst.run.return_value = "pipeline_res"
    mock_ac.return_value = mock_inst

    sdk = ReverseEngineeringSDK()
    res = sdk.run_agents("task")
    assert res == "pipeline_res"
    mock_inst.run.assert_called_once()
