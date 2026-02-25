"""Log download tools for clusters, managed jobs, services, and pools."""

import json

import sky

from skypilot_mcp.app import mcp
from skypilot_mcp.helpers import (
    handle_skypilot_error,
    safe_json_serialize,
)


@mcp.tool(
    name="skypilot_download_logs",
    description=(
        "Download job logs from a cluster to a local directory. "
        "Returns a mapping of job IDs to local log file paths."
    ),
    tags={"job", "logs"},
    annotations={"readOnlyHint": True},
)
@handle_skypilot_error
def skypilot_download_logs(
    cluster_name: str,
    job_ids: list[str] | None = None,
) -> str:
    """Download cluster job logs."""
    result = sky.download_logs(cluster_name, job_ids=job_ids)
    return safe_json_serialize(result)


@mcp.tool(
    name="skypilot_managed_job_download_logs",
    description=(
        "Download logs from a managed job to a local directory. "
        "Specify by name or job_id. Set controller=True to download "
        "controller logs instead of job logs. Optionally specify "
        "local_dir to control where logs are saved."
    ),
    tags={"managed_job", "logs"},
    annotations={"readOnlyHint": True},
)
@handle_skypilot_error
def skypilot_managed_job_download_logs(
    name: str | None = None,
    job_id: int | None = None,
    refresh: bool = False,
    controller: bool = False,
    local_dir: str | None = None,
) -> str:
    """Download managed job logs."""
    kwargs: dict = dict(
        name=name,
        job_id=job_id,
        refresh=refresh,
        controller=controller,
    )
    if local_dir is not None:
        kwargs["local_dir"] = local_dir
    result = sky.jobs.download_logs(**kwargs)
    return safe_json_serialize(result)


@mcp.tool(
    name="skypilot_serve_download_logs",
    description=(
        "Download service logs to a local directory. Optionally filter by "
        "targets ('controller', 'load_balancer', 'replica') and replica_ids."
    ),
    tags={"serve", "logs"},
    annotations={"readOnlyHint": True},
)
@handle_skypilot_error
def skypilot_serve_download_logs(
    service_name: str,
    local_dir: str,
    targets: list[str] | None = None,
    replica_ids: list[int] | None = None,
    tail: int | None = None,
) -> str:
    """Download service logs."""
    sky.serve.sync_down_logs(
        service_name,
        local_dir,
        targets=targets,
        replica_ids=replica_ids,
        tail=tail,
    )
    return json.dumps(
        {
            "service_name": service_name,
            "local_dir": local_dir,
            "message": "Service logs downloaded.",
        }
    )


@mcp.tool(
    name="skypilot_pool_download_logs",
    description=(
        "Download worker pool logs to a local directory. Optionally filter by "
        "targets ('controller', 'load_balancer', 'replica') and worker_ids."
    ),
    tags={"pool", "logs"},
    annotations={"readOnlyHint": True},
)
@handle_skypilot_error
def skypilot_pool_download_logs(
    pool_name: str,
    local_dir: str,
    targets: list[str] | None = None,
    worker_ids: list[int] | None = None,
    tail: int | None = None,
) -> str:
    """Download pool logs."""
    sky.jobs.pool_sync_down_logs(
        pool_name,
        local_dir,
        targets=targets,
        worker_ids=worker_ids,
        tail=tail,
    )
    return json.dumps(
        {
            "pool_name": pool_name,
            "local_dir": local_dir,
            "message": "Pool logs downloaded.",
        }
    )


@mcp.tool(
    name="skypilot_tail_provision_logs",
    description=(
        "Get provisioning logs (provision.log) for a cluster. "
        "Shows the log output from when the cluster was being provisioned. "
        "Optionally specify a worker node index for multi-node clusters. "
        "Returns the last N lines (default 100, set to 0 for all)."
    ),
    tags={"cluster", "logs"},
    annotations={"readOnlyHint": True},
)
@handle_skypilot_error
def skypilot_tail_provision_logs(
    cluster_name: str,
    worker: int | None = None,
    tail: int = 100,
) -> str:
    """Get cluster provisioning logs."""
    import io

    buf = io.StringIO()
    sky.tail_provision_logs(
        cluster_name,
        worker=worker,
        follow=False,
        tail=tail,
        output_stream=buf,
    )
    return buf.getvalue()


@mcp.tool(
    name="skypilot_tail_autostop_logs",
    description=(
        "Get autostop hook logs (autostop_hook.log) for a cluster. "
        "Shows the log output from the autostop hook. "
        "Returns the last N lines (default 100, set to 0 for all)."
    ),
    tags={"cluster", "logs"},
    annotations={"readOnlyHint": True},
)
@handle_skypilot_error
def skypilot_tail_autostop_logs(
    cluster_name: str,
    tail: int = 100,
) -> str:
    """Get cluster autostop logs."""
    import contextlib
    import io

    from skypilot_mcp.helpers import _STDOUT_REDIRECT_LOCK

    buf = io.StringIO()
    # tail_autostop_logs does not accept output_stream, so redirect both
    # stdout and stderr to capture all output reliably.  The lock
    # prevents concurrent tool calls from interleaving output.
    with (
        _STDOUT_REDIRECT_LOCK,
        contextlib.redirect_stdout(buf),
        contextlib.redirect_stderr(buf),
    ):
        exit_code = sky.tail_autostop_logs(
            cluster_name,
            follow=False,
            tail=tail,
        )
    output = buf.getvalue()
    if exit_code:
        raise RuntimeError(
            f"Failed to retrieve autostop logs for cluster "
            f"{cluster_name!r}: exit code {exit_code}."
            + (f"\nOutput: {output}" if output else "")
        )
    return output
