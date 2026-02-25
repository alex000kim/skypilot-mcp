"""Shared helpers for SkyPilot MCP tools."""

import concurrent.futures
import dataclasses
import enum
import functools
import io
import json
import pathlib
import threading
from typing import Any

import sky
from fastmcp.exceptions import ToolError
from sky.exceptions import (
    ApiServerAuthenticationError,
    ApiServerConnectionError,
    APINotSupportedError,
    APIVersionMismatchError,
    CloudError,
    ClusterDoesNotExist,
    ClusterNotUpError,
    ClusterSetUpError,
    CommandError,
    InvalidCloudConfigs,
    InvalidCloudCredentials,
    InvalidClusterNameError,
    NetworkError,
    NoCloudAccessError,
    NotSupportedError,
    PermissionDeniedError,
    PortDoesNotExistError,
    RequestCancelled,
    ResourcesUnavailableError,
    ServerTemporarilyUnavailableError,
    StorageError,
    UserRequestRejectedByPolicy,
    VolumeNotFoundError,
)

try:
    from sky.exceptions import VolumeNotReadyError
except ImportError:
    # VolumeNotReadyError is not available in older skypilot versions;
    # define a placeholder that will never match a raised exception.
    class VolumeNotReadyError(Exception):  # type: ignore[no-redef]
        pass


# Default timeout (seconds) for blocking resolve_request calls.
# Slightly less than the MCP tool timeout (600s) to ensure a clean
# TimeoutError is returned before the MCP framework kills the handler.
DEFAULT_RESOLVE_TIMEOUT = 580

# Lock for functions that redirect stdout/stderr (process-global) to capture
# output from SDK calls that don't support an output_stream parameter.
_STDOUT_REDIRECT_LOCK = threading.Lock()


def create_task_from_yaml(yaml_str: str) -> sky.Task:
    """Create a SkyPilot Task from a YAML string.

    Raises:
        ValueError: If the YAML string is empty or None.
    """
    if not yaml_str or not yaml_str.strip():
        raise ValueError("task_yaml must be a non-empty YAML string.")
    return sky.Task.from_yaml_str(yaml_str)


def load_dag_from_yaml(yaml_str: str):
    """Load a DAG from a YAML string.

    Auto-detects whether the YAML defines a single task, a chain DAG,
    or a job group (multi-document YAML with execution: parallel).

    Raises:
        ValueError: If the YAML string is empty or None.
    """
    if not yaml_str or not yaml_str.strip():
        raise ValueError("task_yaml must be a non-empty YAML string.")
    from sky.utils import dag_utils

    return dag_utils.load_chain_dag_from_yaml_str(yaml_str)


def resolve_request(request_id: str, timeout: int = DEFAULT_RESOLVE_TIMEOUT) -> Any:
    """Block until a SkyPilot request completes and return the result.

    Uses a ThreadPoolExecutor so the future is tracked and the thread is
    reused from a pool rather than leaked on timeout.

    Args:
        request_id: The SkyPilot request ID to wait on.
        timeout: Maximum seconds to wait. Defaults to DEFAULT_RESOLVE_TIMEOUT.

    Raises:
        TimeoutError: If the request does not complete within the timeout.
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(sky.get, request_id)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            future.cancel()
            raise TimeoutError(
                f"Request {request_id} did not complete within {timeout}s. "
                f"The request may still be running on the server. "
                f"Use skypilot_api_status to check its status."
            )


def safe_json_serialize(obj: Any) -> str:
    """Safely serialize complex SkyPilot objects to JSON string.

    Handles Pydantic models, dataclasses, enums, and other
    non-trivially-serializable objects by converting them to dicts/primitives
    before JSON encoding.
    """
    return json.dumps(_make_serializable(obj), indent=2, default=str)


def _make_serializable(obj: Any) -> Any:
    """Recursively convert an object to a JSON-serializable form."""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    # Pydantic v2 models
    if hasattr(obj, "model_dump"):
        return _make_serializable(obj.model_dump())
    # Pydantic v1 models
    if hasattr(obj, "dict") and hasattr(obj, "__fields__"):
        return _make_serializable(obj.dict())
    # Dataclasses — iterate fields directly to avoid deep-copy issues
    # from dataclasses.asdict() which can fail on non-copyable fields.
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {
            f.name: _make_serializable(getattr(obj, f.name))
            for f in dataclasses.fields(obj)
        }
    # Enums
    if isinstance(obj, enum.Enum):
        return obj.value
    # Sets/frozensets — convert to sorted list where possible
    if isinstance(obj, (set, frozenset)):
        try:
            return [_make_serializable(item) for item in sorted(obj)]
        except TypeError:
            return [_make_serializable(item) for item in obj]
    # Dicts — recurse into values
    if isinstance(obj, dict):
        return {str(k): _make_serializable(v) for k, v in obj.items()}
    # Lists/tuples — recurse into elements
    if isinstance(obj, (list, tuple)):
        return [_make_serializable(item) for item in obj]
    # bytes — decode to string
    if isinstance(obj, bytes):
        try:
            return obj.decode("utf-8")
        except UnicodeDecodeError:
            import base64

            return base64.b64encode(obj).decode("ascii")
    # pathlib.Path — convert to string
    if isinstance(obj, pathlib.PurePath):
        return str(obj)
    # Fallback: try json.dumps, then str()
    try:
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        return str(obj)


def capture_cluster_logs(
    cluster_name: str,
    job_id: int | None = None,
    tail: int = 100,
) -> str:
    """Capture cluster job logs into a string.

    Raises RuntimeError if the underlying tail_logs call returns a non-zero
    exit code (indicating failure to retrieve logs).
    """
    buf = io.StringIO()
    exit_code = sky.tail_logs(
        cluster_name, job_id, follow=False, tail=tail, output_stream=buf
    )
    if exit_code:
        raise RuntimeError(
            f"Failed to retrieve logs for cluster {cluster_name!r} "
            f"(job_id={job_id}): tail_logs returned exit code {exit_code}."
        )
    return buf.getvalue()


def capture_managed_job_logs(
    name: str | None = None,
    job_id: int | None = None,
    controller: bool = False,
    refresh: bool = False,
    task: str | int | None = None,
    tail: int = 100,
) -> str:
    """Capture managed job logs into a string.

    Raises RuntimeError if the underlying tail_logs call returns a non-zero
    exit code.
    """
    buf = io.StringIO()
    # sky.jobs.tail_logs uses None for "all lines" and asserts tail > 0
    # when specified, so convert 0 to None.
    sdk_tail = None if tail == 0 else tail
    exit_code = sky.jobs.tail_logs(
        name=name,
        job_id=job_id,
        follow=False,
        controller=controller,
        refresh=refresh,
        task=task,
        tail=sdk_tail,
        output_stream=buf,
    )
    if exit_code:
        identifier = name or job_id
        raise RuntimeError(
            f"Failed to retrieve managed job logs ({identifier}): "
            f"tail_logs returned exit code {exit_code}."
        )
    return buf.getvalue()


def capture_serve_logs(
    service_name: str,
    target: str = "controller",
    replica_id: int | None = None,
    tail: int = 100,
) -> str:
    """Capture service logs into a string."""
    buf = io.StringIO()
    # sky.serve.tail_logs uses None for "all lines"; convert 0 to None.
    sdk_tail = None if tail == 0 else tail
    sky.serve.tail_logs(
        service_name,
        target=target,
        replica_id=replica_id,
        follow=False,
        tail=sdk_tail,
        output_stream=buf,
    )
    return buf.getvalue()


def capture_pool_logs(
    pool_name: str,
    target: str = "controller",
    worker_id: int | None = None,
    tail: int = 100,
) -> str:
    """Capture pool logs into a string."""
    buf = io.StringIO()
    # sky.jobs.pool_tail_logs uses None for "all lines"; convert 0 to None.
    sdk_tail = None if tail == 0 else tail
    sky.jobs.pool_tail_logs(
        pool_name=pool_name,
        target=target,
        worker_id=worker_id,
        follow=False,
        tail=sdk_tail,
        output_stream=buf,
    )
    return buf.getvalue()


def _parse_optimize_target(value: str) -> "sky.OptimizeTarget":
    """Parse an optimize target string to the enum, with a clear error message.

    Raises:
        ValueError: If the value is not a valid OptimizeTarget.
    """
    from sky.utils.common import OptimizeTarget

    try:
        return OptimizeTarget[value.upper()]
    except KeyError:
        valid = ", ".join(t.name for t in OptimizeTarget)
        raise ValueError(
            f"Invalid optimize target: {value!r}. Must be one of: {valid}."
        )


def _parse_status_refresh_mode(value: str) -> Any:
    """Parse a status refresh mode string to the enum.

    Valid values: 'NONE', 'AUTO', 'FORCE' (case-insensitive).

    Raises:
        ValueError: If the value is not a valid StatusRefreshMode.
    """
    from sky.utils.common import StatusRefreshMode

    try:
        return StatusRefreshMode[value.upper()]
    except KeyError:
        valid = ", ".join(m.name for m in StatusRefreshMode)
        raise ValueError(f"Invalid refresh mode: {value!r}. Must be one of: {valid}.")


def _parse_update_mode(value: str) -> Any:
    """Parse an update mode string to the enum, with a clear error message.

    Raises:
        ValueError: If the value is not a valid UpdateMode.
    """
    from sky.serve.serve_utils import UpdateMode

    try:
        return UpdateMode(value)
    except ValueError:
        valid = ", ".join(m.value for m in UpdateMode)
        raise ValueError(f"Invalid update mode: {value!r}. Must be one of: {valid}.")


def handle_skypilot_error(func):
    """Decorator that catches SkyPilot exceptions and raises ToolError.

    This ensures errors are propagated via the MCP protocol's isError flag
    rather than being silently returned as successful JSON responses.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ToolError:
            raise
        # --- Authentication / authorization ---
        except ApiServerAuthenticationError as e:
            raise ToolError(
                f"Authentication required: {e}. Use skypilot_api_login to authenticate."
            ) from e
        except PermissionDeniedError as e:
            raise ToolError(f"Permission denied: {e}") from e
        except UserRequestRejectedByPolicy as e:
            raise ToolError(f"Request rejected by admin policy: {e}") from e
        # --- API server issues ---
        except ApiServerConnectionError as e:
            raise ToolError(f"API server unreachable: {e}") from e
        except ServerTemporarilyUnavailableError as e:
            raise ToolError(
                f"API server temporarily unavailable (retry later): {e}"
            ) from e
        except APIVersionMismatchError as e:
            raise ToolError(f"API version mismatch: {e}") from e
        except APINotSupportedError as e:
            raise ToolError(f"API not supported by server: {e}") from e
        # --- Cluster errors ---
        except ClusterDoesNotExist as e:
            raise ToolError(f"Cluster not found: {e}") from e
        except ClusterNotUpError as e:
            raise ToolError(f"Cluster not up: {e}") from e
        except ClusterSetUpError as e:
            raise ToolError(f"Cluster setup failed: {e}") from e
        except InvalidClusterNameError as e:
            raise ToolError(f"Invalid cluster name: {e}") from e
        # --- Resource / cloud errors ---
        except ResourcesUnavailableError as e:
            raise ToolError(f"Resources unavailable: {e}") from e
        except CloudError as e:
            raise ToolError(f"Cloud provider error: {e}") from e
        except InvalidCloudConfigs as e:
            raise ToolError(f"Invalid cloud configuration: {e}") from e
        except InvalidCloudCredentials as e:
            raise ToolError(f"Invalid cloud credentials: {e}") from e
        except NoCloudAccessError as e:
            raise ToolError(f"No cloud access: {e}") from e
        except NetworkError as e:
            raise ToolError(f"Network error: {e}") from e
        # --- Storage errors ---
        except StorageError as e:
            raise ToolError(f"Storage error: {e}") from e
        # --- Volume errors ---
        except VolumeNotFoundError as e:
            raise ToolError(f"Volume not found: {e}") from e
        except VolumeNotReadyError as e:
            raise ToolError(f"Volume not ready: {e}") from e
        # --- Port errors ---
        except PortDoesNotExistError as e:
            raise ToolError(f"Port not found: {e}") from e
        # --- Command / support errors ---
        except CommandError as e:
            raise ToolError(f"Command error: {e}") from e
        except NotSupportedError as e:
            raise ToolError(f"Not supported: {e}") from e
        except RequestCancelled as e:
            raise ToolError(f"Request cancelled: {e}") from e
        # --- Input / timeout ---
        except ValueError as e:
            raise ToolError(f"Invalid input: {e}") from e
        except TimeoutError as e:
            raise ToolError(f"Timeout: {e}") from e
        except Exception as e:
            raise ToolError(f"{type(e).__name__}: {e}") from e

    return wrapper
