"""Sky Serve (service) management tools."""

import json

import sky

from skypilot_mcp.app import mcp
from skypilot_mcp.helpers import (
    _parse_update_mode,
    capture_serve_logs,
    handle_skypilot_error,
    load_dag_from_yaml,
    resolve_request,
    safe_json_serialize,
)


@mcp.tool(
    name="skypilot_serve_up",
    description=(
        "Launch a new service. Accepts a SkyPilot task YAML string with a "
        "service section defining replicas, readiness probe, etc. "
        "Returns a request_id."
    ),
    tags={"serve"},
    annotations={"destructiveHint": False, "openWorldHint": True},
)
@handle_skypilot_error
def skypilot_serve_up(
    task_yaml: str,
    service_name: str,
) -> str:
    """Launch a service."""
    dag = load_dag_from_yaml(task_yaml)
    request_id = sky.serve.up(dag, service_name=service_name)
    return json.dumps(
        {
            "request_id": str(request_id),
            "service_name": service_name,
            "message": "Service launch submitted. Use skypilot_get_request to check status.",
        }
    )


@mcp.tool(
    name="skypilot_serve_update",
    description=(
        "Update an existing service with a new task configuration. "
        "Set mode to 'rolling' (default) or 'blue_green'. "
        "Returns a request_id."
    ),
    tags={"serve"},
    annotations={"destructiveHint": False, "openWorldHint": True},
)
@handle_skypilot_error
def skypilot_serve_update(
    task_yaml: str,
    service_name: str,
    mode: str = "rolling",
) -> str:
    """Update a service."""
    update_mode = _parse_update_mode(mode)
    dag = load_dag_from_yaml(task_yaml)
    request_id = sky.serve.update(dag, service_name=service_name, mode=update_mode)
    return json.dumps(
        {
            "request_id": str(request_id),
            "service_name": service_name,
            "message": "Service update submitted.",
        }
    )


@mcp.tool(
    name="skypilot_serve_down",
    description=(
        "Tear down service(s). Specify service_names or set delete_all=True. "
        "Set purge=True to force deletion even with errors. Returns a request_id."
    ),
    tags={"serve"},
    annotations={"destructiveHint": True},
)
@handle_skypilot_error
def skypilot_serve_down(
    service_names: list[str] | None = None,
    delete_all: bool = False,
    purge: bool = False,
) -> str:
    """Tear down service(s)."""
    if not service_names and not delete_all:
        raise ValueError("Specify service_names or set delete_all=True.")
    if service_names and delete_all:
        raise ValueError("Specify service_names or delete_all=True, not both.")
    request_id = sky.serve.down(
        service_names=service_names,
        all=delete_all,
        purge=purge,
    )
    return json.dumps(
        {
            "request_id": str(request_id),
            "message": "Service down request submitted.",
        }
    )


@mcp.tool(
    name="skypilot_serve_status",
    description=(
        "Get the status of services. Returns service names, statuses, "
        "replica counts, endpoint URLs, and more. "
        "If no service_names provided, returns all services."
    ),
    tags={"serve"},
    annotations={"readOnlyHint": True},
)
@handle_skypilot_error
def skypilot_serve_status(
    service_names: list[str] | None = None,
) -> str:
    """Get service statuses."""
    request_id = sky.serve.status(service_names=service_names)
    result = resolve_request(request_id)
    return safe_json_serialize(result)


@mcp.tool(
    name="skypilot_serve_logs",
    description=(
        "Get a snapshot of logs from a service component. Target can be "
        "'controller', 'load_balancer', or 'replica'. When target is 'replica', "
        "optionally specify replica_id. Returns the last N lines "
        "(default 100, set to 0 for all). Does not stream/follow."
    ),
    tags={"serve"},
    annotations={"readOnlyHint": True},
)
@handle_skypilot_error
def skypilot_serve_logs(
    service_name: str,
    target: str = "controller",
    replica_id: int | None = None,
    tail: int = 100,
) -> str:
    """Get service logs."""
    return capture_serve_logs(
        service_name=service_name,
        target=target,
        replica_id=replica_id,
        tail=tail,
    )


@mcp.tool(
    name="skypilot_serve_terminate_replica",
    description=(
        "Terminate a specific replica of a service. "
        "Set purge=True to force termination even with errors. "
        "Returns a request_id."
    ),
    tags={"serve"},
    annotations={"destructiveHint": True},
)
@handle_skypilot_error
def skypilot_serve_terminate_replica(
    service_name: str,
    replica_id: int,
    purge: bool = False,
) -> str:
    """Terminate a service replica."""
    request_id = sky.serve.terminate_replica(
        service_name=service_name,
        replica_id=replica_id,
        purge=purge,
    )
    return json.dumps(
        {
            "request_id": str(request_id),
            "service_name": service_name,
            "replica_id": replica_id,
            "message": "Replica termination submitted.",
        }
    )
