"""Cluster lifecycle management tools."""

import json

import sky

from skypilot_mcp.app import mcp
from skypilot_mcp.helpers import (
    _parse_optimize_target,
    _parse_status_refresh_mode,
    handle_skypilot_error,
    load_dag_from_yaml,
    resolve_request,
    safe_json_serialize,
)


@mcp.tool(
    name="skypilot_cluster_status",
    description=(
        "Get the status of SkyPilot clusters. Returns cluster names, statuses, "
        "resource types, autostop settings, and more. "
        "If no cluster_names provided, returns all clusters. "
        "Set refresh to 'NONE' (default, no refresh), 'AUTO' (refresh only "
        "clusters with autostop or spot instances), or 'FORCE' (refresh all)."
    ),
    tags={"cluster"},
    annotations={"readOnlyHint": True},
)
@handle_skypilot_error
def skypilot_cluster_status(
    cluster_names: list[str] | None = None,
    refresh: str = "NONE",
    all_users: bool = False,
) -> str:
    """Get cluster statuses."""
    refresh_mode = _parse_status_refresh_mode(refresh)
    request_id = sky.status(
        cluster_names=cluster_names,
        refresh=refresh_mode,
        all_users=all_users,
    )
    result = resolve_request(request_id)
    return safe_json_serialize(result)


@mcp.tool(
    name="skypilot_cluster_launch",
    description=(
        "Launch a new cluster or submit a task to an existing cluster. "
        "Accepts a SkyPilot task YAML string defining resources, setup, "
        "and run commands. Set optimize_target to 'COST' (default) or 'TIME'. "
        "Set fast=True to skip cloud availability checks for faster provisioning. "
        "Set wait_for to control autostop idle detection: 'jobs_and_ssh' (default), "
        "'jobs', or 'none'. "
        "Returns a request_id — use skypilot_get_request to poll for the result."
    ),
    tags={"cluster"},
    annotations={"destructiveHint": False, "openWorldHint": True},
)
@handle_skypilot_error
def skypilot_cluster_launch(
    task_yaml: str,
    cluster_name: str | None = None,
    retry_until_up: bool = False,
    idle_minutes_to_autostop: int | None = None,
    wait_for: str | None = None,
    down: bool = False,
    dryrun: bool = False,
    no_setup: bool = False,
    fast: bool = False,
    clone_disk_from: str | None = None,
    optimize_target: str = "COST",
) -> str:
    """Launch a cluster with a task."""
    target = _parse_optimize_target(optimize_target)
    dag = load_dag_from_yaml(task_yaml)

    kwargs: dict = dict(
        cluster_name=cluster_name,
        retry_until_up=retry_until_up,
        idle_minutes_to_autostop=idle_minutes_to_autostop,
        down=down,
        dryrun=dryrun,
        no_setup=no_setup,
        fast=fast,
        clone_disk_from=clone_disk_from,
        optimize_target=target,
    )
    if wait_for is not None:
        from sky.skylet.autostop_lib import AutostopWaitFor

        kwargs["wait_for"] = AutostopWaitFor(wait_for)

    request_id = sky.launch(dag, **kwargs)
    return json.dumps(
        {
            "request_id": str(request_id),
            "cluster_name": cluster_name,
            "message": "Launch request submitted. Use skypilot_get_request to check status.",
        }
    )


@mcp.tool(
    name="skypilot_cluster_exec",
    description=(
        "Execute a task on an existing cluster. Syncs workdir and runs commands. "
        "Accepts a SkyPilot task YAML string. Returns a request_id — use "
        "skypilot_get_request to poll for the result."
    ),
    tags={"cluster"},
    annotations={"destructiveHint": False, "openWorldHint": True},
)
@handle_skypilot_error
def skypilot_cluster_exec(
    task_yaml: str,
    cluster_name: str,
    dryrun: bool = False,
    down: bool = False,
) -> str:
    """Execute a task on an existing cluster."""
    dag = load_dag_from_yaml(task_yaml)
    request_id = sky.exec(
        dag,
        cluster_name=cluster_name,
        dryrun=dryrun,
        down=down,
    )
    return json.dumps(
        {
            "request_id": str(request_id),
            "cluster_name": cluster_name,
            "message": "Exec request submitted. Use skypilot_get_request to check status.",
        }
    )


@mcp.tool(
    name="skypilot_cluster_stop",
    description=(
        "Stop a running cluster. Data on attached disks is preserved. "
        "Billing for instances stops but disk charges continue. "
        "Set graceful=True to wait for in-progress data uploads to finish "
        "before stopping (prevents data loss). Returns a request_id."
    ),
    tags={"cluster"},
    annotations={"destructiveHint": True},
)
@handle_skypilot_error
def skypilot_cluster_stop(
    cluster_name: str,
    purge: bool = False,
    graceful: bool = False,
    graceful_timeout: int | None = None,
) -> str:
    """Stop a cluster."""
    request_id = sky.stop(
        cluster_name,
        purge=purge,
        graceful=graceful,
        graceful_timeout=graceful_timeout,
    )
    return json.dumps(
        {
            "request_id": str(request_id),
            "cluster_name": cluster_name,
            "message": "Stop request submitted.",
        }
    )


@mcp.tool(
    name="skypilot_cluster_start",
    description=(
        "Restart a previously stopped cluster. Reattaches preserved disks. "
        "Set wait_for to control autostop idle detection: 'jobs_and_ssh' (default), "
        "'jobs', or 'none'. "
        "Returns a request_id."
    ),
    tags={"cluster"},
    annotations={"destructiveHint": False, "openWorldHint": True},
)
@handle_skypilot_error
def skypilot_cluster_start(
    cluster_name: str,
    idle_minutes_to_autostop: int | None = None,
    wait_for: str | None = None,
    retry_until_up: bool = False,
    down: bool = False,
    force: bool = False,
) -> str:
    """Start a stopped cluster."""
    kwargs: dict = dict(
        idle_minutes_to_autostop=idle_minutes_to_autostop,
        retry_until_up=retry_until_up,
        down=down,
        force=force,
    )
    if wait_for is not None:
        from sky.skylet.autostop_lib import AutostopWaitFor

        kwargs["wait_for"] = AutostopWaitFor(wait_for)

    request_id = sky.start(cluster_name, **kwargs)
    return json.dumps(
        {
            "request_id": str(request_id),
            "cluster_name": cluster_name,
            "message": "Start request submitted.",
        }
    )


@mcp.tool(
    name="skypilot_cluster_down",
    description=(
        "Tear down a cluster completely. All associated resources are deleted "
        "and data on attached disks is lost. Returns a request_id."
    ),
    tags={"cluster"},
    annotations={"destructiveHint": True},
)
@handle_skypilot_error
def skypilot_cluster_down(
    cluster_name: str,
    purge: bool = False,
) -> str:
    """Tear down a cluster."""
    request_id = sky.down(
        cluster_name,
        purge=purge,
    )
    return json.dumps(
        {
            "request_id": str(request_id),
            "cluster_name": cluster_name,
            "message": "Down request submitted.",
        }
    )


@mcp.tool(
    name="skypilot_cluster_autostop",
    description=(
        "Set an autostop timer for a cluster. The cluster will automatically "
        "stop (or tear down if down=True) after being idle for the specified "
        "number of minutes. Set idle_minutes to -1 to disable. "
        "Set wait_for to control idle detection: 'jobs_and_ssh' (default), "
        "'jobs', or 'none'. "
        "Set hook to a shell command to run on the cluster before autostop. "
        "Returns a request_id."
    ),
    tags={"cluster"},
    annotations={"idempotentHint": True},
)
@handle_skypilot_error
def skypilot_cluster_autostop(
    cluster_name: str,
    idle_minutes: int,
    wait_for: str | None = None,
    down: bool = False,
    hook: str | None = None,
    hook_timeout: int | None = None,
) -> str:
    """Set autostop for a cluster."""
    kwargs: dict = dict(idle_minutes=idle_minutes, down=down)
    if wait_for is not None:
        from sky.skylet.autostop_lib import AutostopWaitFor

        kwargs["wait_for"] = AutostopWaitFor(wait_for)
    if hook is not None:
        kwargs["hook"] = hook
    if hook_timeout is not None:
        kwargs["hook_timeout"] = hook_timeout

    request_id = sky.autostop(cluster_name, **kwargs)
    return json.dumps(
        {
            "request_id": str(request_id),
            "cluster_name": cluster_name,
            "message": f"Autostop set to {idle_minutes} minutes.",
        }
    )


@mcp.tool(
    name="skypilot_cluster_endpoints",
    description=(
        "Get the endpoint(s) for a cluster. Optionally filter by port number "
        "or port name. Returns a mapping of port numbers to endpoint URLs."
    ),
    tags={"cluster"},
    annotations={"readOnlyHint": True},
)
@handle_skypilot_error
def skypilot_cluster_endpoints(
    cluster_name: str,
    port: int | str | None = None,
) -> str:
    """Get cluster endpoints."""
    request_id = sky.endpoints(cluster_name, port=port)
    result = resolve_request(request_id)
    return safe_json_serialize(result)
