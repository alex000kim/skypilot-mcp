"""Tests for cluster job tools — parameter validation logic."""

import pytest
from fastmcp.exceptions import ToolError


def test_cancel_rejects_both_job_ids_and_cancel_all(mock_sky):
    from skypilot_mcp.tools.jobs import skypilot_job_cancel

    with pytest.raises(ToolError, match="not both"):
        skypilot_job_cancel("c", job_ids=[1], cancel_all=True)


def test_cancel_rejects_neither_job_ids_nor_cancel_all(mock_sky):
    from skypilot_mcp.tools.jobs import skypilot_job_cancel

    with pytest.raises(ToolError, match="cancel_all"):
        skypilot_job_cancel("c")


def test_job_logs_nonzero_exit_raises(mock_sky):
    """capture_cluster_logs should raise RuntimeError on non-zero exit."""
    from skypilot_mcp.tools.jobs import skypilot_job_logs

    mock_sky.tail_logs.return_value = 1
    with pytest.raises(ToolError, match="Failed to retrieve logs"):
        skypilot_job_logs("c")
