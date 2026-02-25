"""Managed job tools (auto-recovery, spot instances)."""

import json

import sky

from skypilot_mcp.app import mcp
from skypilot_mcp.helpers import (
    capture_managed_job_logs,
    handle_skypilot_error,
    load_dag_from_yaml,
    resolve_request,
    safe_json_serialize,
)


@mcp.tool(
    name="skypilot_managed_job_launch",
    description=(
        "Launch a managed job with automatic recovery from spot preemptions "
        "and hardware failures. Accepts a SkyPilot task YAML string (single task "
        "or multi-document YAML for job groups with parallel execution). "
        "Set pool to target a specific worker pool. Set num_jobs to launch "
        "multiple copies of the same job. Returns a request_id."
    ),
    tags={"managed_job"},
    annotations={"destructiveHint": False, "openWorldHint": True},
)
@handle_skypilot_error
def skypilot_managed_job_launch(
    task_yaml: str,
    name: str | None = None,
    pool: str | None = None,
    num_jobs: int | None = None,
) -> str:
    """Launch a managed job."""
    dag = load_dag_from_yaml(task_yaml)
    request_id = sky.jobs.launch(dag, name=name, pool=pool, num_jobs=num_jobs)
    return json.dumps(
        {
            "request_id": str(request_id),
            "name": name,
            "pool": pool,
            "message": "Managed job launch submitted. Use skypilot_get_request to check status.",
        }
    )


@mcp.tool(
    name="skypilot_managed_job_queue",
    description=(
        "List managed jobs and their statuses (v2 API). Returns job IDs, "
        "names, statuses, submission times, recovery information, total "
        "count, and status counts. Set refresh=True to fetch the latest "
        "state from the cluster (slower but up-to-date). Supports sorting "
        "and pagination via limit, sort_by, and sort_order parameters."
    ),
    tags={"managed_job"},
    annotations={"readOnlyHint": True},
)
@handle_skypilot_error
def skypilot_managed_job_queue(
    refresh: bool,
    skip_finished: bool = False,
    all_users: bool = False,
    job_ids: list[int] | None = None,
    limit: int | None = None,
    fields: list[str] | None = None,
    sort_by: str | None = None,
    sort_order: str | None = None,
) -> str:
    """Get managed job queue using the v2 API."""
    request_id = sky.jobs.queue_v2(
        refresh=refresh,
        skip_finished=skip_finished,
        all_users=all_users,
        job_ids=job_ids,
        limit=limit,
        fields=fields,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    result = resolve_request(request_id)
    # queue_v2 returns a tuple; unpack defensively.
    if isinstance(result, (list, tuple)) and len(result) >= 4:
        records, total_count, status_counts, filtered_count = (
            result[0],
            result[1],
            result[2],
            result[3],
        )
    else:
        return safe_json_serialize(result)
    return safe_json_serialize(
        {
            "jobs": records,
            "total_count": total_count,
            "status_counts": status_counts,
            "filtered_count": filtered_count,
        }
    )


@mcp.tool(
    name="skypilot_managed_job_queue_v1",
    description=(
        "List managed jobs and their statuses (v1 API). Returns a flat list "
        "of job records without pagination or sorting support. Use this for "
        "compatibility with older API servers or when the simpler return "
        "format is preferred. Set refresh=True to fetch the latest state "
        "from the cluster."
    ),
    tags={"managed_job"},
    annotations={"readOnlyHint": True},
)
@handle_skypilot_error
def skypilot_managed_job_queue_v1(
    refresh: bool,
    skip_finished: bool = False,
    all_users: bool = False,
    job_ids: list[int] | None = None,
) -> str:
    """Get managed job queue using the v1 API."""
    request_id = sky.jobs.queue(
        refresh=refresh,
        skip_finished=skip_finished,
        all_users=all_users,
        job_ids=job_ids,
    )
    result = resolve_request(request_id)
    return safe_json_serialize(result)


@mcp.tool(
    name="skypilot_managed_job_cancel",
    description=(
        "Cancel managed jobs. Provide exactly one of: name, job_ids, "
        "cancel_all=True, or pool (mutually exclusive). Set all_users=True to "
        "cancel jobs from all users. Set graceful=True to wait for in-progress "
        "data uploads before cancelling. Returns a request_id."
    ),
    tags={"managed_job"},
    annotations={"destructiveHint": True},
)
@handle_skypilot_error
def skypilot_managed_job_cancel(
    name: str | None = None,
    job_ids: list[int] | None = None,
    cancel_all: bool = False,
    all_users: bool = False,
    pool: str | None = None,
    graceful: bool = False,
    graceful_timeout: int | None = None,
) -> str:
    """Cancel managed jobs."""
    specifiers = [name is not None, job_ids is not None, cancel_all, pool is not None]
    if sum(specifiers) != 1:
        raise ValueError(
            "Specify exactly one of: name, job_ids, cancel_all=True, or pool."
        )
    request_id = sky.jobs.cancel(
        name=name,
        job_ids=job_ids,
        all=cancel_all,
        all_users=all_users,
        pool=pool,
        graceful=graceful,
        graceful_timeout=graceful_timeout,
    )
    return json.dumps(
        {
            "request_id": str(request_id),
            "message": "Managed job cancel request submitted.",
        }
    )


@mcp.tool(
    name="skypilot_managed_job_logs",
    description=(
        "Get a snapshot of logs from a managed job. "
        "Returns the last N lines (default 100, set to 0 for all). "
        "Does not stream/follow. Specify by name or job_id. "
        "Set controller=True to view the jobs controller logs instead. "
        "Set task to view logs for a specific task in a JobGroup "
        "(task name or 0-based index)."
    ),
    tags={"managed_job"},
    annotations={"readOnlyHint": True},
)
@handle_skypilot_error
def skypilot_managed_job_logs(
    name: str | None = None,
    job_id: int | None = None,
    controller: bool = False,
    refresh: bool = False,
    task: str | int | None = None,
    tail: int = 100,
) -> str:
    """Get managed job logs."""
    return capture_managed_job_logs(
        name=name,
        job_id=job_id,
        controller=controller,
        refresh=refresh,
        task=task,
        tail=tail,
    )
