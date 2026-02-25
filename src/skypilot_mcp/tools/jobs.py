"""Cluster job management tools."""

import json

import sky

from skypilot_mcp.app import mcp
from skypilot_mcp.helpers import (
    capture_cluster_logs,
    handle_skypilot_error,
    resolve_request,
    safe_json_serialize,
)


@mcp.tool(
    name="skypilot_job_queue",
    description=(
        "List jobs on a cluster's job queue. Returns job IDs, names, statuses, "
        "submission times, and resource usage."
    ),
    tags={"job"},
    annotations={"readOnlyHint": True},
)
@handle_skypilot_error
def skypilot_job_queue(
    cluster_name: str,
    skip_finished: bool = False,
    all_users: bool = False,
) -> str:
    """Get the job queue of a cluster."""
    request_id = sky.queue(
        cluster_name, skip_finished=skip_finished, all_users=all_users
    )
    result = resolve_request(request_id)
    return safe_json_serialize(result)


@mcp.tool(
    name="skypilot_job_status",
    description=(
        "Get the status of specific jobs on a cluster. "
        "If no job_ids provided, returns the status of the latest job."
    ),
    tags={"job"},
    annotations={"readOnlyHint": True},
)
@handle_skypilot_error
def skypilot_job_status(
    cluster_name: str,
    job_ids: list[int] | None = None,
) -> str:
    """Get job statuses."""
    request_id = sky.job_status(cluster_name, job_ids=job_ids)
    result = resolve_request(request_id)
    return safe_json_serialize(result)


@mcp.tool(
    name="skypilot_job_cancel",
    description=(
        "Cancel jobs on a cluster. Provide either job_ids to cancel specific "
        "jobs, or set cancel_all=True to cancel all jobs (mutually exclusive). "
        "Set all_users=True to cancel jobs from all users. Returns a request_id."
    ),
    tags={"job"},
    annotations={"destructiveHint": True},
)
@handle_skypilot_error
def skypilot_job_cancel(
    cluster_name: str,
    job_ids: list[int] | None = None,
    cancel_all: bool = False,
    all_users: bool = False,
) -> str:
    """Cancel jobs on a cluster."""
    if cancel_all and job_ids:
        raise ValueError("Specify either job_ids or cancel_all=True, not both.")
    if not cancel_all and not job_ids:
        raise ValueError("Specify job_ids or set cancel_all=True.")
    request_id = sky.cancel(
        cluster_name, all=cancel_all, all_users=all_users, job_ids=job_ids
    )
    return json.dumps(
        {
            "request_id": str(request_id),
            "cluster_name": cluster_name,
            "message": "Cancel request submitted.",
        }
    )


@mcp.tool(
    name="skypilot_job_logs",
    description=(
        "Get a snapshot of logs from a job running on a cluster. "
        "Returns the last N lines (default 100, set to 0 for all). "
        "Does not stream/follow logs. "
        "If no job_id is provided, returns logs for the latest job."
    ),
    tags={"job"},
    annotations={"readOnlyHint": True},
)
@handle_skypilot_error
def skypilot_job_logs(
    cluster_name: str,
    job_id: int | None = None,
    tail: int = 100,
) -> str:
    """Get job logs."""
    return capture_cluster_logs(cluster_name, job_id=job_id, tail=tail)
