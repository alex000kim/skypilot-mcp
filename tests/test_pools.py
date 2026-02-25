"""Tests for worker pool tools — validation and update mode logic."""

import pytest
from fastmcp.exceptions import ToolError
from sky.serve.serve_utils import UpdateMode
from unittest.mock import MagicMock, patch


def test_apply_resolves_blue_green_mode(mock_sky):
    """mode='blue_green' should resolve to the real UpdateMode enum."""
    from skypilot_mcp.tools.pools import skypilot_pool_apply

    mock_dag = MagicMock()
    with patch("skypilot_mcp.tools.pools.load_dag_from_yaml", return_value=mock_dag):
        skypilot_pool_apply(
            pool_name="p",
            task_yaml="resources:\n  accelerators: A100:4",
            mode="blue_green",
        )
    assert mock_sky.jobs.pool_apply.call_args[1]["mode"] == UpdateMode.BLUE_GREEN


def test_apply_invalid_mode_raises(mock_sky):
    from skypilot_mcp.tools.pools import skypilot_pool_apply

    with pytest.raises(ToolError, match="Invalid"):
        skypilot_pool_apply(pool_name="p", mode="bad")


def test_down_rejects_both(mock_sky):
    from skypilot_mcp.tools.pools import skypilot_pool_down

    with pytest.raises(ToolError, match="not both"):
        skypilot_pool_down(pool_names=["p"], delete_all=True)


def test_down_rejects_neither(mock_sky):
    from skypilot_mcp.tools.pools import skypilot_pool_down

    with pytest.raises(ToolError, match="Specify pool_names"):
        skypilot_pool_down()
