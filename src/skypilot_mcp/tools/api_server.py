"""API server management and request polling tools."""

import json

import sky

from skypilot_mcp.app import mcp
from skypilot_mcp.helpers import (
    handle_skypilot_error,
    resolve_request,
    safe_json_serialize,
)


@mcp.tool(
    name="skypilot_api_info",
    description=(
        "Get SkyPilot API server information including health status, "
        "version, commit hash, and authentication details."
    ),
    tags={"api"},
    annotations={"readOnlyHint": True},
)
@handle_skypilot_error
def skypilot_api_info() -> str:
    """Get API server info."""
    info = sky.api_info()
    return safe_json_serialize(info)


@mcp.tool(
    name="skypilot_api_status",
    description=(
        "List pending and running API requests. Optionally filter by "
        "specific request_ids, cluster_name, or fields. "
        "Set all_status=True to include finished requests. "
        "Use limit to cap the number of results."
    ),
    tags={"api"},
    annotations={"readOnlyHint": True},
)
@handle_skypilot_error
def skypilot_api_status(
    request_ids: list[str] | None = None,
    all_status: bool = False,
    limit: int | None = None,
    fields: list[str] | None = None,
    cluster_name: str | None = None,
) -> str:
    """List API requests."""
    result = sky.api_status(
        request_ids=request_ids,
        all_status=all_status,
        limit=limit,
        fields=fields,
        cluster_name=cluster_name,
    )
    return safe_json_serialize(result)


@mcp.tool(
    name="skypilot_api_cancel",
    description=(
        "Cancel pending API requests. Specify request_ids to cancel specific "
        "requests. Returns a request_id for the cancel operation itself."
    ),
    tags={"api"},
    annotations={"destructiveHint": True},
)
@handle_skypilot_error
def skypilot_api_cancel(
    request_ids: list[str] | None = None,
    all_users: bool = False,
) -> str:
    """Cancel API requests."""
    request_id = sky.api_cancel(request_ids=request_ids, all_users=all_users)
    return json.dumps(
        {
            "request_id": str(request_id),
            "message": "API cancel request submitted.",
        }
    )


@mcp.tool(
    name="skypilot_get_request",
    description=(
        "Wait for a SkyPilot request to complete and return its result. "
        "Use this after calling tools that return a request_id "
        "(e.g., skypilot_cluster_launch, skypilot_cluster_stop, etc.). "
        "This call blocks until the request finishes."
    ),
    tags={"api"},
    annotations={"readOnlyHint": True, "openWorldHint": True},
    timeout=600,
)
@handle_skypilot_error
def skypilot_get_request(request_id: str) -> str:
    """Wait for and return the result of a SkyPilot request."""
    result = resolve_request(request_id)
    return safe_json_serialize(result)


@mcp.tool(
    name="skypilot_stream_and_get",
    description=(
        "Wait for a SkyPilot request to complete while capturing its log "
        "output. Unlike skypilot_get_request (which only returns the final "
        "result), this also returns the streaming logs produced during "
        "execution — useful for long-running operations like launch, exec, "
        "or managed job launch. Returns a JSON object with 'result' and "
        "'logs' fields. Set tail to limit how many trailing log lines are "
        "captured (default: all). Set follow=False to return immediately "
        "with whatever logs are available. Use log_path instead of "
        "request_id to stream from a specific log file on the API server."
    ),
    tags={"api"},
    annotations={"readOnlyHint": True, "openWorldHint": True},
    timeout=600,
)
@handle_skypilot_error
def skypilot_stream_and_get(
    request_id: str,
    tail: int | None = None,
    follow: bool = True,
    log_path: str | None = None,
) -> str:
    """Stream logs and return the result of a SkyPilot request."""
    import io

    buf = io.StringIO()
    result = sky.stream_and_get(
        request_id,
        log_path=log_path,
        follow=follow,
        tail=tail,
        output_stream=buf,
    )
    return safe_json_serialize(
        {
            "result": result,
            "logs": buf.getvalue(),
        }
    )


@mcp.tool(
    name="skypilot_api_start",
    description=(
        "Start the SkyPilot API server. Set deploy=True for deployment mode "
        "(fully utilizes resources). Optionally enable metrics collection "
        "and basic auth. Note: foreground mode is not supported via MCP "
        "as it would block the server permanently."
    ),
    tags={"api"},
    annotations={"destructiveHint": False, "openWorldHint": True},
)
@handle_skypilot_error
def skypilot_api_start(
    deploy: bool = False,
    host: str = "127.0.0.1",
    metrics: bool = False,
    metrics_port: int | None = None,
    enable_basic_auth: bool = False,
) -> str:
    """Start the API server."""
    sky.api_start(
        deploy=deploy,
        host=host,
        foreground=False,
        metrics=metrics,
        metrics_port=metrics_port,
        enable_basic_auth=enable_basic_auth,
    )
    return json.dumps({"message": "API server started."})


@mcp.tool(
    name="skypilot_api_stop",
    description=(
        "Stop the SkyPilot API server. Only works for locally hosted "
        "API servers. Will raise an error for remote API servers."
    ),
    tags={"api"},
    annotations={"destructiveHint": True},
)
@handle_skypilot_error
def skypilot_api_stop() -> str:
    """Stop the API server."""
    sky.api_stop()
    return json.dumps({"message": "API server stopped."})


@mcp.tool(
    name="skypilot_api_server_logs",
    description=(
        "Get SkyPilot API server logs. Returns a snapshot of the server "
        "log output. Set tail to limit the number of lines returned."
    ),
    tags={"api"},
    annotations={"readOnlyHint": True},
)
@handle_skypilot_error
def skypilot_api_server_logs(
    tail: int | None = 100,
) -> str:
    """Get API server logs."""
    import contextlib
    import io

    from skypilot_mcp.helpers import _STDOUT_REDIRECT_LOCK

    buf = io.StringIO()
    # api_server_logs does not accept output_stream, so redirect both
    # stdout and stderr to capture all output reliably.  The lock
    # prevents concurrent tool calls from interleaving output.
    with (
        _STDOUT_REDIRECT_LOCK,
        contextlib.redirect_stdout(buf),
        contextlib.redirect_stderr(buf),
    ):
        sky.api_server_logs(follow=False, tail=tail)
    return buf.getvalue()


@mcp.tool(
    name="skypilot_api_login",
    description=(
        "Log in to a remote SkyPilot API server. Sets the endpoint globally "
        "so all subsequent SkyPilot calls use it. Set relogin=True to force "
        "re-authentication with OAuth2."
    ),
    tags={"api"},
    annotations={"destructiveHint": False},
)
@handle_skypilot_error
def skypilot_api_login(
    endpoint: str | None = None,
    relogin: bool = False,
    service_account_token: str | None = None,
) -> str:
    """Log in to API server."""
    sky.api_login(
        endpoint=endpoint,
        relogin=relogin,
        service_account_token=service_account_token,
    )
    return json.dumps({"message": "Logged in to API server."})


@mcp.tool(
    name="skypilot_api_logout",
    description=(
        "Log out of the remote SkyPilot API server. Clears all cookies "
        "and settings. Only works for remote API servers."
    ),
    tags={"api"},
    annotations={"destructiveHint": True},
)
@handle_skypilot_error
def skypilot_api_logout() -> str:
    """Log out of API server."""
    sky.api_logout()
    return json.dumps({"message": "Logged out of API server."})
