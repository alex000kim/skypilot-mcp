"""Tests for managed job tools — validation, defensive unpacking, log capture."""

import json

import pytest
from fastmcp.exceptions import ToolError


# -- Cancel: mutual exclusivity -------------------------------------------


def test_cancel_rejects_multiple_specifiers(mock_sky):
    from skypilot_mcp.tools.managed_jobs import skypilot_managed_job_cancel

    with pytest.raises(ToolError, match="Specify exactly one of"):
        skypilot_managed_job_cancel(name="j", job_ids=[1])


def test_cancel_rejects_no_specifier(mock_sky):
    from skypilot_mcp.tools.managed_jobs import skypilot_managed_job_cancel

    with pytest.raises(ToolError, match="Specify exactly one of"):
        skypilot_managed_job_cancel()


# -- Queue v2: defensive tuple unpacking -----------------------------------


def test_queue_v2_unpacks_4_tuple(mock_sky):
    """When result is a 4-tuple, unpack into structured JSON."""
    mock_sky.get.return_value = (
        [{"job_id": 1}],  # records
        1,  # total_count
        {"RUNNING": 1},  # status_counts
        1,  # filtered_count
    )
    from skypilot_mcp.tools.managed_jobs import skypilot_managed_job_queue

    result = json.loads(skypilot_managed_job_queue(refresh=False))
    assert result["total_count"] == 1
    assert result["jobs"] == [{"job_id": 1}]
    assert result["status_counts"] == {"RUNNING": 1}


def test_queue_v2_falls_back_on_unexpected_format(mock_sky):
    """When result is not a 4-tuple, serialize as-is."""
    mock_sky.get.return_value = {"unexpected": "format"}
    from skypilot_mcp.tools.managed_jobs import skypilot_managed_job_queue

    result = json.loads(skypilot_managed_job_queue(refresh=False))
    assert result["unexpected"] == "format"


# -- Logs: stream capture and controller/task params -----------------------


def test_logs_captures_output(mock_sky):
    def fake_tail(**kw):
        kw["output_stream"].write("log line\n")
        return 0

    mock_sky.jobs.tail_logs.side_effect = fake_tail
    from skypilot_mcp.tools.managed_jobs import skypilot_managed_job_logs

    assert "log line" in skypilot_managed_job_logs(name="j")


def test_logs_passes_controller_and_task(mock_sky):
    def fake_tail(**kw):
        kw["output_stream"].write("ok\n")
        return 0

    mock_sky.jobs.tail_logs.side_effect = fake_tail
    from skypilot_mcp.tools.managed_jobs import skypilot_managed_job_logs

    skypilot_managed_job_logs(name="j", controller=True, task=2)
    kw = mock_sky.jobs.tail_logs.call_args[1]
    assert kw["controller"] is True
    assert kw["task"] == 2
