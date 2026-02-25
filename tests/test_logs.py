"""Tests for log tools — conditional parameter handling."""


def test_managed_job_download_logs_omits_local_dir_when_none(mock_sky):
    """local_dir should not be passed to SDK when not provided."""
    mock_sky.jobs.download_logs.return_value = {1: "/tmp/logs/mjob-1"}
    from skypilot_mcp.tools.logs import skypilot_managed_job_download_logs

    skypilot_managed_job_download_logs(job_id=1, controller=True)
    kw = mock_sky.jobs.download_logs.call_args[1]
    assert "local_dir" not in kw
    assert kw["controller"] is True


def test_managed_job_download_logs_passes_local_dir_when_set(mock_sky):
    """local_dir should be passed when explicitly provided."""
    mock_sky.jobs.download_logs.return_value = {1: "/custom/logs/mjob-1"}
    from skypilot_mcp.tools.logs import skypilot_managed_job_download_logs

    skypilot_managed_job_download_logs(name="j", local_dir="/custom/logs")
    assert mock_sky.jobs.download_logs.call_args[1]["local_dir"] == "/custom/logs"
