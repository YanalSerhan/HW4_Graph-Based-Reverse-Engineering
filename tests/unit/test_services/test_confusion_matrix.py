"""
Tests for confusion_matrix.py
"""

from unittest.mock import MagicMock, patch

import pytest

import graph_rev_eng.services.confusion_matrix as cm


@pytest.fixture
def mock_environment():
    """Mock the external dependencies of confusion_matrix.py."""
    with (
        patch("graph_rev_eng.services.confusion_matrix.ConfigManager") as mock_config,
        patch("graph_rev_eng.services.confusion_matrix.ApiGatekeeper"),
        patch("graph_rev_eng.services.confusion_matrix.GraphLoader") as mock_loader,
        patch("graph_rev_eng.services.confusion_matrix.Path.write_text") as mock_write,
        patch("graph_rev_eng.services.confusion_matrix.Path.rglob") as mock_rglob,
    ):
        # Setup config mock
        config_inst = mock_config.get_instance.return_value
        config_inst.get_rate_limits.return_value = {"rpm_limit": 100, "tpm_limit": 1000}
        config_inst.get_api_key.return_value = "fake_key"

        # Setup loader mock
        mock_graph = MagicMock()
        mock_graph.edges = []
        mock_loader.return_value.load.return_value = mock_graph

        # Setup rglob mock to return empty list
        mock_rglob.return_value = []

        yield mock_write


def test_confusion_matrix_counts(mock_environment):
    """Test that TP/FP/TN/FN are counted correctly given known predictions vs ground truth."""
    # We will test 4 facts: 1 TP, 1 FP, 1 TN, 1 FN
    test_facts = [
        ("Fact TP", True),  # Expected True, Predict True -> TP
        ("Fact FP", False),  # Expected False, Predict True -> FP
        ("Fact TN", False),  # Expected False, Predict False -> TN
        ("Fact FN", True),  # Expected True, Predict False -> FN
    ]

    def stub_llm(prompt):
        if "Fact TP" in prompt or "Fact FP" in prompt:
            return "TRUE"
        return "FALSE"

    with (
        patch("graph_rev_eng.services.confusion_matrix.FACTS", test_facts),
        patch("graph_rev_eng.services.confusion_matrix.OpenAILLM", return_value=stub_llm),
    ):
        cm.main()

        # Check written markdown for correct metrics
        mock_write = mock_environment
        mock_write.assert_called_once()
        md_content = mock_write.call_args[0][0]

        assert "- **True Positives (TP):** 1" in md_content
        assert "- **False Positives (FP):** 1" in md_content
        assert "- **True Negatives (TN):** 1" in md_content
        assert "- **False Negatives (FN):** 1" in md_content


def test_confusion_matrix_precision_recall_f1(mock_environment):
    """Test precision/recall/F1 computation with a known set
    (e.g. 3 TP, 1 FP, 0 FN -> precision 0.75, recall 1.0)."""
    test_facts = [
        ("Fact TP1", True),  # TP
        ("Fact TP2", True),  # TP
        ("Fact TP3", True),  # TP
        ("Fact FP1", False),  # FP
        ("Fact TN1", False),  # TN
    ]

    def stub_llm(prompt):
        if "Fact TN1" in prompt:
            return "FALSE"
        return "TRUE"  # Everything else predicted TRUE

    with (
        patch("graph_rev_eng.services.confusion_matrix.FACTS", test_facts),
        patch("graph_rev_eng.services.confusion_matrix.OpenAILLM", return_value=stub_llm),
    ):
        cm.main()

        mock_write = mock_environment
        md_content = mock_write.call_args[0][0]

        # 3 TP, 1 FP, 0 FN
        # Precision: 3 / (3 + 1) = 0.75
        # Recall: 3 / (3 + 0) = 1.0
        # F1: 2 * (0.75 * 1.0) / (0.75 + 1.0) = 1.5 / 1.75 = 0.857... (0.86)

        assert "- **True Positives (TP):** 3" in md_content
        assert "- **Precision:** 0.75" in md_content
        assert "- **Recall:** 1.00" in md_content
        assert "- **F1 Score:** 0.86" in md_content


def test_confusion_matrix_all_correct(mock_environment):
    """Test edge case: all correct predictions -> F1 = 1.0."""
    test_facts = [
        ("Fact TP1", True),  # TP
        ("Fact TN1", False),  # TN
    ]

    def stub_llm(prompt):
        if "Fact TP1" in prompt:
            return "TRUE"
        return "FALSE"

    with (
        patch("graph_rev_eng.services.confusion_matrix.FACTS", test_facts),
        patch("graph_rev_eng.services.confusion_matrix.OpenAILLM", return_value=stub_llm),
    ):
        cm.main()

        mock_write = mock_environment
        md_content = mock_write.call_args[0][0]

        assert "- **True Positives (TP):** 1" in md_content
        assert "- **False Positives (FP):** 0" in md_content
        assert "- **True Negatives (TN):** 1" in md_content
        assert "- **False Negatives (FN):** 0" in md_content

        assert "- **Precision:** 1.00" in md_content
        assert "- **Recall:** 1.00" in md_content
        assert "- **F1 Score:** 1.00" in md_content
