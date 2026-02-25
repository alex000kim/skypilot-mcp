"""Configuration and utility tools."""

import json

import sky
from sky.client.sdk import dashboard as sky_dashboard

from skypilot_mcp.app import mcp
from skypilot_mcp.helpers import (
    handle_skypilot_error,
    resolve_request,
    safe_json_serialize,
)


@mcp.tool(
    name="skypilot_reload_config",
    description=(
        "Reload the SkyPilot client-side configuration from "
        "~/.sky/config.yaml. Use after making manual changes to the "
        "config file."
    ),
    tags={"config"},
    annotations={"idempotentHint": True},
)
@handle_skypilot_error
def skypilot_reload_config() -> str:
    """Reload SkyPilot configuration."""
    sky.reload_config()
    return json.dumps({"message": "Configuration reloaded."})


@mcp.tool(
    name="skypilot_workspaces",
    description=(
        "List available SkyPilot workspaces. Returns workspace names "
        "and their configurations."
    ),
    tags={"config"},
    annotations={"readOnlyHint": True},
)
@handle_skypilot_error
def skypilot_workspaces() -> str:
    """Get workspaces."""
    request_id = sky.workspaces()
    result = resolve_request(request_id)
    return safe_json_serialize(result)


@mcp.tool(
    name="skypilot_dashboard",
    description=(
        "Open the SkyPilot dashboard in the default web browser. "
        "Optionally specify a starting page."
    ),
    tags={"config"},
    annotations={"readOnlyHint": True},
)
@handle_skypilot_error
def skypilot_dashboard(
    starting_page: str | None = None,
) -> str:
    """Open the SkyPilot dashboard."""
    sky_dashboard(starting_page=starting_page)
    return json.dumps({"message": "Dashboard opened in browser."})


@mcp.tool(
    name="skypilot_jobs_dashboard",
    description=(
        "Open the managed jobs dashboard in the default web browser. "
        "Shows a dedicated view for monitoring managed jobs."
    ),
    tags={"managed_job", "config"},
    annotations={"readOnlyHint": True},
)
@handle_skypilot_error
def skypilot_jobs_dashboard() -> str:
    """Open the jobs dashboard."""
    sky.jobs.dashboard()
    return json.dumps({"message": "Jobs dashboard opened in browser."})
