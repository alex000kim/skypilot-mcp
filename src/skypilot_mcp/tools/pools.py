"""Worker pool management tools."""

import json

import sky

from skypilot_mcp.app import mcp
from skypilot_mcp.helpers import (
    _parse_update_mode,
    capture_pool_logs,
    handle_skypilot_error,
    load_dag_from_yaml,
    resolve_request,
    safe_json_serialize,
)


@mcp.tool(
    name="skypilot_pool_apply",
    description=(
        "Create or update a worker pool. A worker pool is a long-lived set of "
        "compute resources that can host multiple managed jobs. Accepts a SkyPilot "
        "task YAML string defining the pool's resources. Set mode to 'rolling' "
        "(default) or 'blue_green' for the update strategy. Returns a request_id."
    ),
    tags={"pool"},
    annotations={"destructiveHint": False, "openWorldHint": True},
)
@handle_skypilot_error
def skypilot_pool_apply(
    pool_name: str,
    task_yaml: str | None = None,
    mode: str = "rolling",
    workers: int | None = None,
) -> str:
    """Apply a configuration to a worker pool."""
    update_mode = _parse_update_mode(mode)
    dag = load_dag_from_yaml(task_yaml) if task_yaml else None
    request_id = sky.jobs.pool_apply(
        task=dag,
        pool_name=pool_name,
        mode=update_mode,
        workers=workers,
    )
    return json.dumps(
        {
            "request_id": str(request_id),
            "pool_name": pool_name,
            "message": "Pool apply request submitted.",
        }
    )


@mcp.tool(
    name="skypilot_pool_status",
    description=(
        "Get the status of worker pools. Returns pool names, worker counts, "
        "statuses, and resource information. If no pool_names provided, "
        "returns all pools."
    ),
    tags={"pool"},
    annotations={"readOnlyHint": True},
)
@handle_skypilot_error
def skypilot_pool_status(
    pool_names: list[str] | None = None,
) -> str:
    """Get pool statuses."""
    request_id = sky.jobs.pool_status(pool_names=pool_names)
    result = resolve_request(request_id)
    return safe_json_serialize(result)


@mcp.tool(
    name="skypilot_pool_down",
    description=(
        "Delete worker pool(s). Specify pool_names or set delete_all=True. "
        "Set purge=True to force deletion even with errors. Returns a request_id."
    ),
    tags={"pool"},
    annotations={"destructiveHint": True},
)
@handle_skypilot_error
def skypilot_pool_down(
    pool_names: list[str] | None = None,
    delete_all: bool = False,
    purge: bool = False,
) -> str:
    """Delete worker pool(s)."""
    if not pool_names and not delete_all:
        raise ValueError("Specify pool_names or set delete_all=True.")
    if pool_names and delete_all:
        raise ValueError("Specify pool_names or delete_all=True, not both.")
    request_id = sky.jobs.pool_down(
        pool_names=pool_names,
        all=delete_all,
        purge=purge,
    )
    return json.dumps(
        {
            "request_id": str(request_id),
            "message": "Pool down request submitted.",
        }
    )


@mcp.tool(
    name="skypilot_pool_logs",
    description=(
        "Get a snapshot of logs from a worker pool. Target can be 'controller', "
        "'load_balancer', or 'replica'. Optionally specify a worker_id. "
        "Returns the last N lines (default 100, set to 0 for all). "
        "Does not stream/follow."
    ),
    tags={"pool"},
    annotations={"readOnlyHint": True},
)
@handle_skypilot_error
def skypilot_pool_logs(
    pool_name: str,
    target: str = "controller",
    worker_id: int | None = None,
    tail: int = 100,
) -> str:
    """Get pool logs."""
    return capture_pool_logs(
        pool_name=pool_name,
        target=target,
        worker_id=worker_id,
        tail=tail,
    )
