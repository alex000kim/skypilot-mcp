"""Tests for cluster tools — validation and enum conversion logic only."""

from unittest.mock import MagicMock, patch

import pytest
from fastmcp.exceptions import ToolError
from sky.skylet.autostop_lib import AutostopWaitFor
from sky.utils.common import OptimizeTarget, StatusRefreshMode


def test_launch_resolves_optimize_target(mock_sky):
    """optimize_target string should be converted to the real enum."""
    from skypilot_mcp.tools.cluster import skypilot_cluster_launch

    mock_dag = MagicMock()
    with patch("skypilot_mcp.tools.cluster.load_dag_from_yaml", return_value=mock_dag):
        skypilot_cluster_launch(task_yaml="run: echo hi", optimize_target="TIME")

    call_kwargs = mock_sky.launch.call_args[1]
    assert call_kwargs["optimize_target"] == OptimizeTarget.TIME


def test_launch_resolves_wait_for(mock_sky):
    """wait_for string should be converted to the real AutostopWaitFor enum."""
    from skypilot_mcp.tools.cluster import skypilot_cluster_launch

    mock_dag = MagicMock()
    with patch("skypilot_mcp.tools.cluster.load_dag_from_yaml", return_value=mock_dag):
        skypilot_cluster_launch(
            task_yaml="run: echo hi",
            cluster_name="c",
            wait_for="jobs",
        )

    assert mock_sky.launch.call_args[1]["wait_for"] == AutostopWaitFor.JOBS


def test_start_resolves_wait_for(mock_sky):
    """wait_for on start should also use the real enum."""
    from skypilot_mcp.tools.cluster import skypilot_cluster_start

    skypilot_cluster_start("c", wait_for="jobs_and_ssh")
    assert mock_sky.start.call_args[1]["wait_for"] == AutostopWaitFor.JOBS_AND_SSH


def test_autostop_resolves_wait_for(mock_sky):
    from skypilot_mcp.tools.cluster import skypilot_cluster_autostop

    skypilot_cluster_autostop("c", idle_minutes=10, wait_for="none")
    assert mock_sky.autostop.call_args[1]["wait_for"] == AutostopWaitFor.NONE


def test_status_resolves_refresh_mode(mock_sky):
    """refresh string should be converted to the real StatusRefreshMode enum."""
    from skypilot_mcp.tools.cluster import skypilot_cluster_status

    mock_sky.get.return_value = []
    skypilot_cluster_status(refresh="FORCE")
    assert mock_sky.status.call_args[1]["refresh"] == StatusRefreshMode.FORCE


def test_status_invalid_refresh_raises(mock_sky):
    from skypilot_mcp.tools.cluster import skypilot_cluster_status

    with pytest.raises(ToolError, match="Invalid"):
        skypilot_cluster_status(refresh="INVALID")


def test_launch_empty_yaml_raises(mock_sky):
    from skypilot_mcp.tools.cluster import skypilot_cluster_launch

    with pytest.raises(ToolError, match="Invalid input"):
        skypilot_cluster_launch(task_yaml="")
