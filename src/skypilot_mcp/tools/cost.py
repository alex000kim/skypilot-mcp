"""Cost reporting tools."""

import sky

from skypilot_mcp.app import mcp
from skypilot_mcp.helpers import (
    handle_skypilot_error,
    resolve_request,
    safe_json_serialize,
)


@mcp.tool(
    name="skypilot_cost_report",
    description=(
        "Get cost reports for all clusters, including those that have been "
        "terminated. Shows estimated costs based on resource types and usage "
        "duration. Optionally filter by number of days."
    ),
    tags={"cost"},
    annotations={"readOnlyHint": True},
)
@handle_skypilot_error
def skypilot_cost_report(
    days: int | None = None,
) -> str:
    """Get cluster cost reports."""
    request_id = sky.cost_report(days=days)
    result = resolve_request(request_id)
    return safe_json_serialize(result)
