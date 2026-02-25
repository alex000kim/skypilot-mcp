"""Tests for DAG tools — validation error handling."""

import pytest
from fastmcp.exceptions import ToolError
from unittest.mock import MagicMock, patch


def test_validate_error_raises_tool_error(mock_sky):
    mock_dag = MagicMock()
    mock_sky.validate.side_effect = ValueError("Invalid task config")

    with patch("skypilot_mcp.tools.dag.load_dag_from_yaml", return_value=mock_dag):
        from skypilot_mcp.tools.dag import skypilot_validate

        with pytest.raises(ToolError, match="Invalid input"):
            skypilot_validate(task_yaml="bad config")


def test_optimize_empty_yaml_raises(mock_sky):
    from skypilot_mcp.tools.dag import skypilot_optimize

    with pytest.raises(ToolError, match="Invalid input"):
        skypilot_optimize(task_yaml="")
