"""Tests for Sky Serve tools — validation and update mode logic."""

import pytest
from fastmcp.exceptions import ToolError
from sky.serve.serve_utils import UpdateMode
from unittest.mock import MagicMock, patch


def test_update_resolves_rolling_mode(mock_sky):
    """mode='rolling' should resolve to the real UpdateMode enum."""
    from skypilot_mcp.tools.serve import skypilot_serve_update

    mock_dag = MagicMock()
    with patch("skypilot_mcp.tools.serve.load_dag_from_yaml", return_value=mock_dag):
        skypilot_serve_update(
            task_yaml="run: python app.py",
            service_name="s",
            mode="rolling",
        )
    assert mock_sky.serve.update.call_args[1]["mode"] == UpdateMode.ROLLING


def test_update_resolves_blue_green_mode(mock_sky):
    from skypilot_mcp.tools.serve import skypilot_serve_update

    mock_dag = MagicMock()
    with patch("skypilot_mcp.tools.serve.load_dag_from_yaml", return_value=mock_dag):
        skypilot_serve_update(
            task_yaml="run: python app.py",
            service_name="s",
            mode="blue_green",
        )
    assert mock_sky.serve.update.call_args[1]["mode"] == UpdateMode.BLUE_GREEN


def test_update_invalid_mode_raises(mock_sky):
    from skypilot_mcp.tools.serve import skypilot_serve_update

    mock_dag = MagicMock()
    with patch("skypilot_mcp.tools.serve.load_dag_from_yaml", return_value=mock_dag):
        with pytest.raises(ToolError, match="Invalid"):
            skypilot_serve_update(
                task_yaml="run: echo",
                service_name="s",
                mode="bad",
            )


def test_down_rejects_both(mock_sky):
    from skypilot_mcp.tools.serve import skypilot_serve_down

    with pytest.raises(ToolError, match="not both"):
        skypilot_serve_down(service_names=["s"], delete_all=True)


def test_down_rejects_neither(mock_sky):
    from skypilot_mcp.tools.serve import skypilot_serve_down

    with pytest.raises(ToolError, match="Specify service_names"):
        skypilot_serve_down()
