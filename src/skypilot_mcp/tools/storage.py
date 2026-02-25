"""Storage management tools."""

import json

import sky

from skypilot_mcp.app import mcp
from skypilot_mcp.helpers import (
    handle_skypilot_error,
    resolve_request,
    safe_json_serialize,
)


@mcp.tool(
    name="skypilot_storage_ls",
    description="List all SkyPilot-managed storage objects (cloud buckets).",
    tags={"storage"},
    annotations={"readOnlyHint": True},
)
@handle_skypilot_error
def skypilot_storage_ls() -> str:
    """List storage objects."""
    request_id = sky.storage_ls()
    result = resolve_request(request_id)
    return safe_json_serialize(result)


@mcp.tool(
    name="skypilot_storage_delete",
    description=(
        "Delete a SkyPilot-managed storage object (cloud bucket). Returns a request_id."
    ),
    tags={"storage"},
    annotations={"destructiveHint": True},
)
@handle_skypilot_error
def skypilot_storage_delete(name: str) -> str:
    """Delete a storage object."""
    request_id = sky.storage_delete(name)
    return json.dumps(
        {
            "request_id": str(request_id),
            "name": name,
            "message": "Storage delete request submitted.",
        }
    )
