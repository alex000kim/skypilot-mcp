"""Shared fixtures for SkyPilot MCP tests."""

# ---- Patch missing exceptions early (before any test module imports) ----
# The source code references exceptions that may not exist in the installed
# version of SkyPilot. We synthesize any missing ones so that module-level
# imports in helpers.py succeed during test collection.
import sky.exceptions as _sky_exc

_MISSING_EXCEPTIONS = [
    "VolumeNotReadyError",
]
for _name in _MISSING_EXCEPTIONS:
    if not hasattr(_sky_exc, _name):
        _cls = type(_name, (Exception,), {})
        setattr(_sky_exc, _name, _cls)
# ---- End early patching ----

import pytest  # noqa: E402


@pytest.fixture
def mock_sky(monkeypatch):
    """Replace ``sky`` with a MagicMock in every tool / helper module.

    Only the SDK calls are mocked; real SkyPilot enums and exceptions are
    still used so that tests catch incompatibilities with the installed SDK.
    """
    from unittest.mock import MagicMock

    mock = MagicMock()

    # --- Sensible defaults so tools don't crash on basic calls -----------
    mock.api_info.return_value = {
        "status": "healthy",
        "api_version": "1",
        "version": "0.11.0",
        "commit": "abc1234",
    }
    mock.api_status.return_value = []

    # Request-id pattern for async operations
    mock.status.return_value = "req-status-001"
    mock.launch.return_value = "req-launch-001"
    mock.exec.return_value = "req-exec-001"
    mock.stop.return_value = "req-stop-001"
    mock.start.return_value = "req-start-001"
    mock.down.return_value = "req-down-001"
    mock.autostop.return_value = "req-autostop-001"
    mock.queue.return_value = "req-queue-001"
    mock.job_status.return_value = "req-jobstatus-001"
    mock.cancel.return_value = "req-cancel-001"
    mock.cost_report.return_value = "req-cost-001"
    mock.storage_ls.return_value = "req-storage-ls-001"
    mock.storage_delete.return_value = "req-storage-del-001"
    mock.api_cancel.return_value = "req-api-cancel-001"
    mock.endpoints.return_value = "req-endpoints-001"
    mock.optimize.return_value = "req-optimize-001"
    mock.validate.return_value = None
    mock.download_logs.return_value = {"1": "/tmp/logs/job-1"}
    mock.tail_provision_logs.return_value = 0
    mock.tail_autostop_logs.return_value = 0

    # Blocking resolve default
    mock.get.return_value = []

    # API server lifecycle
    for attr in (
        "api_start",
        "api_stop",
        "api_server_logs",
        "api_login",
        "api_logout",
        "stream_and_get",
        "reload_config",
        "dashboard",
    ):
        getattr(mock, attr).return_value = None
    mock.workspaces.return_value = "req-workspaces-001"

    # Infra
    for attr in (
        "check",
        "enabled_clouds",
        "list_accelerators",
        "list_accelerator_counts",
        "kubernetes_node_info",
        "realtime_kubernetes_gpu_availability",
        "kubernetes_label_gpus",
        "status_kubernetes",
        "local_up",
        "local_down",
        "ssh_up",
        "ssh_down",
        "realtime_slurm_gpu_availability",
        "slurm_node_info",
    ):
        getattr(mock, attr).return_value = f"req-{attr}-001"

    # Managed jobs
    mock.jobs = MagicMock()
    mock.jobs.launch.return_value = "req-mjob-launch-001"
    mock.jobs.queue.return_value = "req-mjob-queue-001"
    mock.jobs.queue_v2.return_value = "req-mjob-queue-v2-001"
    mock.jobs.cancel.return_value = "req-mjob-cancel-001"
    mock.jobs.tail_logs.return_value = 0
    mock.jobs.download_logs.return_value = {1: "/tmp/logs/mjob-1"}
    mock.jobs.dashboard.return_value = None
    mock.jobs.pool_apply.return_value = "req-pool-apply-001"
    mock.jobs.pool_status.return_value = "req-pool-status-001"
    mock.jobs.pool_down.return_value = "req-pool-down-001"
    mock.jobs.pool_tail_logs.return_value = None
    mock.jobs.pool_sync_down_logs.return_value = None

    # Serve
    mock.serve = MagicMock()
    mock.serve.up.return_value = "req-serve-up-001"
    mock.serve.update.return_value = "req-serve-update-001"
    mock.serve.down.return_value = "req-serve-down-001"
    mock.serve.status.return_value = "req-serve-status-001"
    mock.serve.tail_logs.return_value = None
    mock.serve.terminate_replica.return_value = "req-serve-terminate-001"
    mock.serve.sync_down_logs.return_value = None

    # Volumes
    mock.volumes = MagicMock()
    mock.volumes.apply.return_value = "req-vol-apply-001"
    mock.volumes.ls.return_value = "req-vol-ls-001"
    mock.volumes.delete.return_value = "req-vol-delete-001"
    mock.volumes.validate.return_value = None

    # Task creation
    mock.Task.from_yaml_str.return_value = MagicMock()

    # Patch sky in all tool modules and helper/app modules
    for module_path in [
        "skypilot_mcp.tools.api_server",
        "skypilot_mcp.tools.cluster",
        "skypilot_mcp.tools.config",
        "skypilot_mcp.tools.cost",
        "skypilot_mcp.tools.dag",
        "skypilot_mcp.tools.infra",
        "skypilot_mcp.tools.jobs",
        "skypilot_mcp.tools.logs",
        "skypilot_mcp.tools.managed_jobs",
        "skypilot_mcp.tools.pools",
        "skypilot_mcp.tools.serve",
        "skypilot_mcp.tools.storage",
        "skypilot_mcp.tools.volumes",
        "skypilot_mcp.helpers",
        "skypilot_mcp.app",
    ]:
        monkeypatch.setattr(f"{module_path}.sky", mock)

    # Patch the directly-imported sky_dashboard in config module
    monkeypatch.setattr("skypilot_mcp.tools.config.sky_dashboard", mock.dashboard)

    return mock
