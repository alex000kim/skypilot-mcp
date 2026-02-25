"""DAG optimization and validation tools."""

import json

import sky

from skypilot_mcp.app import mcp
from skypilot_mcp.helpers import (
    _parse_optimize_target,
    handle_skypilot_error,
    load_dag_from_yaml,
    resolve_request,
    safe_json_serialize,
)


@mcp.tool(
    name="skypilot_optimize",
    description=(
        "Find the best execution plan for a task. Analyzes available clouds, "
        "regions, and instance types to find the optimal placement. "
        "Set minimize to 'COST' (default) or 'TIME'. Returns the optimized "
        "DAG with the best resources selected."
    ),
    tags={"dag"},
    annotations={"readOnlyHint": True},
)
@handle_skypilot_error
def skypilot_optimize(
    task_yaml: str,
    minimize: str = "COST",
) -> str:
    """Optimize a task DAG."""
    target = _parse_optimize_target(minimize)
    dag = load_dag_from_yaml(task_yaml)
    request_id = sky.optimize(dag, minimize=target)
    result = resolve_request(request_id)
    return safe_json_serialize(result)


@mcp.tool(
    name="skypilot_validate",
    description=(
        "Validate a task configuration without launching it. Checks that "
        "file paths (workdir, file_mounts) exist locally and that the task "
        "specification is valid on the server side. Raises an error if "
        "validation fails, returns success message otherwise."
    ),
    tags={"dag"},
    annotations={"readOnlyHint": True},
)
@handle_skypilot_error
def skypilot_validate(
    task_yaml: str,
    workdir_only: bool = False,
) -> str:
    """Validate a task DAG."""
    dag = load_dag_from_yaml(task_yaml)
    sky.validate(dag, workdir_only=workdir_only)
    return json.dumps({"status": "valid", "message": "Task validation passed."})
