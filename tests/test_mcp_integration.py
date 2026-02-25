"""MCP protocol integration tests.

These tests use the real FastMCP Client to call tools through the MCP
protocol, verifying tool registration, schema correctness, JSON responses,
and error handling — things the previous mock-heavy tests never covered.
"""

import json

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

# Trigger tool registration by importing the server module.
import skypilot_mcp.server  # noqa: F401

from skypilot_mcp.app import mcp as mcp_app

# Every tool the server is supposed to expose.
EXPECTED_TOOLS = {
    # API server
    "skypilot_api_info",
    "skypilot_api_status",
    "skypilot_api_cancel",
    "skypilot_get_request",
    "skypilot_stream_and_get",
    "skypilot_api_start",
    "skypilot_api_stop",
    "skypilot_api_server_logs",
    "skypilot_api_login",
    "skypilot_api_logout",
    # Cluster
    "skypilot_cluster_status",
    "skypilot_cluster_launch",
    "skypilot_cluster_exec",
    "skypilot_cluster_stop",
    "skypilot_cluster_start",
    "skypilot_cluster_down",
    "skypilot_cluster_autostop",
    "skypilot_cluster_endpoints",
    # Config
    "skypilot_reload_config",
    "skypilot_workspaces",
    "skypilot_dashboard",
    "skypilot_jobs_dashboard",
    # Cost
    "skypilot_cost_report",
    # DAG
    "skypilot_optimize",
    "skypilot_validate",
    # Infra
    "skypilot_check",
    "skypilot_enabled_clouds",
    "skypilot_list_accelerators",
    "skypilot_list_accelerator_counts",
    "skypilot_kubernetes_node_info",
    "skypilot_realtime_gpu_availability",
    "skypilot_kubernetes_label_gpus",
    "skypilot_status_kubernetes",
    "skypilot_local_up",
    "skypilot_local_down",
    "skypilot_ssh_up",
    "skypilot_ssh_down",
    "skypilot_realtime_slurm_gpu_availability",
    "skypilot_slurm_node_info",
    # Jobs
    "skypilot_job_queue",
    "skypilot_job_status",
    "skypilot_job_cancel",
    "skypilot_job_logs",
    # Logs
    "skypilot_download_logs",
    "skypilot_managed_job_download_logs",
    "skypilot_serve_download_logs",
    "skypilot_pool_download_logs",
    "skypilot_tail_provision_logs",
    "skypilot_tail_autostop_logs",
    # Managed jobs
    "skypilot_managed_job_launch",
    "skypilot_managed_job_queue",
    "skypilot_managed_job_queue_v1",
    "skypilot_managed_job_cancel",
    "skypilot_managed_job_logs",
    # Pools
    "skypilot_pool_apply",
    "skypilot_pool_status",
    "skypilot_pool_down",
    "skypilot_pool_logs",
    # Serve
    "skypilot_serve_up",
    "skypilot_serve_update",
    "skypilot_serve_down",
    "skypilot_serve_status",
    "skypilot_serve_logs",
    "skypilot_serve_terminate_replica",
    # Storage
    "skypilot_storage_ls",
    "skypilot_storage_delete",
    # Volumes
    "skypilot_volume_apply",
    "skypilot_volume_ls",
    "skypilot_volume_delete",
    "skypilot_volume_validate",
}


@pytest.fixture
async def client(mock_sky):
    """Create a FastMCP client connected to the real MCP app with sky mocked."""
    async with Client(mcp_app) as c:
        yield c


# -- Tool discovery --------------------------------------------------------


async def test_all_tools_registered(client):
    """Every expected tool should be discoverable via the MCP protocol."""
    tools = await client.list_tools()
    registered = {t.name for t in tools}
    missing = EXPECTED_TOOLS - registered
    assert not missing, f"Tools not registered: {missing}"


async def test_no_unexpected_tools(client):
    """No tools beyond the expected set should be registered."""
    tools = await client.list_tools()
    registered = {t.name for t in tools}
    extra = registered - EXPECTED_TOOLS
    assert not extra, f"Unexpected tools registered: {extra}"


async def test_tools_have_descriptions(client):
    """Every tool should have a non-empty description."""
    tools = await client.list_tools()
    for tool in tools:
        assert tool.description, f"Tool {tool.name} has no description"


# -- Tool invocation via MCP protocol -------------------------------------


async def test_call_api_info(client, mock_sky):
    """Calling a read-only tool through MCP should return valid JSON."""
    result = await client.call_tool("skypilot_api_info", {})
    parsed = json.loads(result.content[0].text)
    assert parsed["status"] == "healthy"
    assert parsed["version"] == "0.11.0"


async def test_call_cluster_status(client, mock_sky):
    """Cluster status should return serialized list through MCP."""
    mock_sky.get.return_value = [
        {"name": "test-cluster", "status": "UP"},
    ]
    result = await client.call_tool("skypilot_cluster_status", {})
    parsed = json.loads(result.content[0].text)
    assert len(parsed) == 1
    assert parsed[0]["name"] == "test-cluster"


async def test_call_cluster_stop(client, mock_sky):
    """A mutating tool should return a request_id through MCP."""
    result = await client.call_tool(
        "skypilot_cluster_stop",
        {"cluster_name": "my-cluster"},
    )
    parsed = json.loads(result.content[0].text)
    assert "request_id" in parsed


async def test_call_job_cancel_validation_error(client, mock_sky):
    """Validation errors should propagate as ToolError through MCP."""
    with pytest.raises(ToolError, match="not both"):
        await client.call_tool(
            "skypilot_job_cancel",
            {"cluster_name": "c", "job_ids": [1], "cancel_all": True},
        )


async def test_call_serve_down_validation_error(client, mock_sky):
    """Missing required params should propagate as ToolError through MCP."""
    with pytest.raises(ToolError, match="Specify service_names"):
        await client.call_tool("skypilot_serve_down", {})


async def test_call_with_stream_capture(client, mock_sky):
    """stream_and_get should capture logs and return them in the response."""

    def mock_stream(
        request_id, log_path=None, follow=True, tail=None, output_stream=None
    ):
        output_stream.write("Launching cluster...\nDone.\n")
        return {"job_id": 1, "status": "SUCCEEDED"}

    mock_sky.stream_and_get.side_effect = mock_stream

    result = await client.call_tool(
        "skypilot_stream_and_get",
        {"request_id": "req-launch-001"},
    )
    parsed = json.loads(result.content[0].text)
    assert "Launching cluster" in parsed["logs"]
    assert parsed["result"]["status"] == "SUCCEEDED"


# -- Tool annotations / tags ----------------------------------------------


async def test_read_only_tools_annotated(client):
    """Read-only tools should be annotated with readOnlyHint=True."""
    tools = await client.list_tools()
    tools_by_name = {t.name: t for t in tools}

    read_only_tools = [
        "skypilot_api_info",
        "skypilot_cluster_status",
        "skypilot_cluster_endpoints",
        "skypilot_job_queue",
        "skypilot_serve_status",
    ]
    for name in read_only_tools:
        tool = tools_by_name[name]
        annotations = tool.annotations
        assert annotations is not None, f"{name} missing annotations"
        assert annotations.readOnlyHint is True, f"{name} should be readOnlyHint=True"


async def test_destructive_tools_annotated(client):
    """Destructive tools should be annotated with destructiveHint=True."""
    tools = await client.list_tools()
    tools_by_name = {t.name: t for t in tools}

    destructive_tools = [
        "skypilot_cluster_stop",
        "skypilot_cluster_down",
        "skypilot_serve_down",
        "skypilot_job_cancel",
    ]
    for name in destructive_tools:
        tool = tools_by_name[name]
        annotations = tool.annotations
        assert annotations is not None, f"{name} missing annotations"
        assert annotations.destructiveHint is True, (
            f"{name} should be destructiveHint=True"
        )
