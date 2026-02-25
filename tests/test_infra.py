"""Tests for infra tools — defensive unpacking logic."""

import json


def test_status_kubernetes_unpacks_4_tuple(mock_sky):
    """When result is a 4-tuple, unpack into structured JSON."""
    mock_sky.get.return_value = (
        [{"name": "cluster-1"}],
        [{"name": "other-1"}],
        [{"job_id": 1}],
        "default-context",
    )
    from skypilot_mcp.tools.infra import skypilot_status_kubernetes

    result = json.loads(skypilot_status_kubernetes())
    assert result["context"] == "default-context"
    assert result["clusters"] == [{"name": "cluster-1"}]
    assert result["other_clusters"] == [{"name": "other-1"}]
    assert result["managed_jobs"] == [{"job_id": 1}]


def test_status_kubernetes_falls_back_on_unexpected_format(mock_sky):
    """When result is not a 4-tuple, serialize as-is."""
    mock_sky.get.return_value = {"unexpected": "format"}
    from skypilot_mcp.tools.infra import skypilot_status_kubernetes

    result = json.loads(skypilot_status_kubernetes())
    assert result["unexpected"] == "format"


def test_check_converts_infra_list_to_tuple(mock_sky):
    """infra list should be converted to a tuple for the SDK."""
    mock_sky.get.return_value = {"aws": ["us-east-1"]}
    from skypilot_mcp.tools.infra import skypilot_check

    skypilot_check(infra=["aws", "gcp"])
    mock_sky.check.assert_called_once_with(
        infra_list=("aws", "gcp"),
        verbose=False,
        workspace=None,
    )
