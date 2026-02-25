"""Tests for helper functions.

These tests exercise real logic: serialization, error mapping, enum parsing,
input validation, timeout handling, and log capture.  Enum parsers use the
real SkyPilot enum classes (not mocks) so they catch SDK incompatibilities.
"""

import dataclasses
import enum
import json
import pathlib
from datetime import datetime

import pytest
from fastmcp.exceptions import ToolError
from pydantic import BaseModel
from sky.serve.serve_utils import UpdateMode
from sky.utils.common import OptimizeTarget, StatusRefreshMode

from skypilot_mcp.helpers import (
    _make_serializable,
    _parse_optimize_target,
    _parse_status_refresh_mode,
    _parse_update_mode,
    capture_managed_job_logs,
    create_task_from_yaml,
    handle_skypilot_error,
    load_dag_from_yaml,
    resolve_request,
    safe_json_serialize,
)


# ---------------------------------------------------------------------------
# safe_json_serialize / _make_serializable
# ---------------------------------------------------------------------------


def test_serialize_dict():
    parsed = json.loads(safe_json_serialize({"key": "value", "num": 42}))
    assert parsed == {"key": "value", "num": 42}


def test_serialize_non_json_type_uses_str():
    parsed = json.loads(safe_json_serialize({"time": datetime(2024, 1, 1)}))
    assert "2024" in parsed["time"]


def test_serialize_list():
    assert json.loads(safe_json_serialize([1, 2, 3])) == [1, 2, 3]


def test_serialize_none():
    assert safe_json_serialize(None) == "null"


def test_serialize_pydantic_v2_model():
    class StatusResponse(BaseModel):
        name: str
        status: str
        resources: dict

    obj = StatusResponse(name="c1", status="UP", resources={"gpu": "V100"})
    parsed = json.loads(safe_json_serialize(obj))
    assert parsed["name"] == "c1"
    assert parsed["resources"]["gpu"] == "V100"


def test_serialize_list_of_pydantic_models():
    class JobRecord(BaseModel):
        job_id: int
        job_name: str

    objs = [JobRecord(job_id=1, job_name="train"), JobRecord(job_id=2, job_name="eval")]
    parsed = json.loads(safe_json_serialize(objs))
    assert len(parsed) == 2
    assert parsed[0]["job_id"] == 1


def test_serialize_dataclass():
    @dataclasses.dataclass
    class CostEntry:
        cluster_name: str
        total_cost: float

    parsed = json.loads(safe_json_serialize(CostEntry("test", 12.50)))
    assert parsed == {"cluster_name": "test", "total_cost": 12.50}


def test_serialize_nested_pydantic():
    class Inner(BaseModel):
        value: int

    class Outer(BaseModel):
        name: str
        inner: Inner

    parsed = json.loads(safe_json_serialize(Outer(name="test", inner=Inner(value=42))))
    assert parsed["inner"]["value"] == 42


def test_make_serializable_enum():
    class Status(enum.Enum):
        UP = "UP"

    assert _make_serializable(Status.UP) == "UP"


def test_make_serializable_set():
    assert _make_serializable({3, 1, 2}) == [1, 2, 3]


def test_make_serializable_frozenset():
    assert _make_serializable(frozenset(["b", "a", "c"])) == ["a", "b", "c"]


def test_make_serializable_set_unsortable():
    result = _make_serializable({1, "a"})
    assert isinstance(result, list) and set(result) == {1, "a"}


def test_make_serializable_bytes_utf8():
    assert _make_serializable(b"hello world") == "hello world"


def test_make_serializable_bytes_non_utf8():
    import base64

    result = _make_serializable(b"\xff\xfe")
    assert base64.b64decode(result) == b"\xff\xfe"


def test_make_serializable_pathlib_path():
    assert _make_serializable(pathlib.Path("/tmp/my/path")) == "/tmp/my/path"


def test_make_serializable_pure_posix_path():
    assert _make_serializable(pathlib.PurePosixPath("/etc/config")) == "/etc/config"


# ---------------------------------------------------------------------------
# resolve_request
# ---------------------------------------------------------------------------


def test_resolve_request_timeout(mock_sky):
    import time

    def blocking_get(request_id):
        time.sleep(5)
        return []

    mock_sky.get.side_effect = blocking_get
    with pytest.raises(TimeoutError, match="did not complete within"):
        resolve_request("req-slow-001", timeout=1)


def test_resolve_request_propagates_errors(mock_sky):
    mock_sky.get.side_effect = RuntimeError("connection lost")
    with pytest.raises(RuntimeError, match="connection lost"):
        resolve_request("req-err-001")


def test_resolve_request_success(mock_sky):
    mock_sky.get.return_value = [{"name": "cluster-1"}]
    assert resolve_request("req-ok-001") == [{"name": "cluster-1"}]


def test_resolve_request_none_result(mock_sky):
    mock_sky.get.return_value = None
    assert resolve_request("req-none-001") is None


# ---------------------------------------------------------------------------
# handle_skypilot_error  (tests real exception classes from sky.exceptions)
# ---------------------------------------------------------------------------


def test_handle_error_value_error():
    @handle_skypilot_error
    def f():
        raise ValueError("bad input")

    with pytest.raises(ToolError, match="Invalid input: bad input"):
        f()


def test_handle_error_timeout():
    @handle_skypilot_error
    def f():
        raise TimeoutError("took too long")

    with pytest.raises(ToolError, match="Timeout: took too long"):
        f()


def test_handle_error_generic_exception():
    @handle_skypilot_error
    def f():
        raise RuntimeError("something broke")

    with pytest.raises(ToolError, match="RuntimeError: something broke"):
        f()


def test_handle_error_passes_through_tool_error():
    @handle_skypilot_error
    def f():
        raise ToolError("already handled")

    with pytest.raises(ToolError, match="already handled"):
        f()


def test_handle_error_returns_on_success():
    @handle_skypilot_error
    def f():
        return "ok"

    assert f() == "ok"


@pytest.mark.parametrize(
    "exc_cls,exc_args,expected_match",
    [
        ("ApiServerAuthenticationError", ("bad token",), "Authentication required"),
        ("PermissionDeniedError", ("not allowed",), "Permission denied"),
        ("ApiServerConnectionError", ("cannot connect",), "API server unreachable"),
        ("ClusterDoesNotExist", ("my-cluster",), "Cluster not found"),
        ("ResourcesUnavailableError", ("no A100s",), "Resources unavailable"),
        ("StorageError", ("bucket issue",), "Storage error"),
        ("NotSupportedError", ("feature X",), "Not supported"),
        ("RequestCancelled", ("user cancelled",), "Request cancelled"),
        ("VolumeNotFoundError", ("my-vol",), "Volume not found"),
        (
            "ServerTemporarilyUnavailableError",
            ("overloaded",),
            "temporarily unavailable",
        ),
        (
            "UserRequestRejectedByPolicy",
            ("denied",),
            "Request rejected by admin policy",
        ),
    ],
)
def test_handle_error_sky_exceptions(exc_cls, exc_args, expected_match):
    """Each SkyPilot exception should map to the correct ToolError message."""
    import sky.exceptions as sky_exc

    cls = getattr(sky_exc, exc_cls)

    @handle_skypilot_error
    def f():
        raise cls(*exc_args)

    with pytest.raises(ToolError, match=expected_match):
        f()


# ---------------------------------------------------------------------------
# create_task_from_yaml / load_dag_from_yaml  (input validation)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad_input", ["", "   \n  ", None])
def test_create_task_from_yaml_rejects_empty(mock_sky, bad_input):
    with pytest.raises(ValueError, match="non-empty YAML"):
        create_task_from_yaml(bad_input)


@pytest.mark.parametrize("bad_input", ["", "   \n  "])
def test_load_dag_from_yaml_rejects_empty(mock_sky, bad_input):
    with pytest.raises(ValueError, match="non-empty YAML"):
        load_dag_from_yaml(bad_input)


# ---------------------------------------------------------------------------
# _parse_optimize_target  (uses REAL sky.utils.common.OptimizeTarget)
# ---------------------------------------------------------------------------


def test_parse_optimize_target_cost():
    assert _parse_optimize_target("COST") == OptimizeTarget.COST


def test_parse_optimize_target_time():
    assert _parse_optimize_target("TIME") == OptimizeTarget.TIME


def test_parse_optimize_target_case_insensitive():
    assert _parse_optimize_target("cost") == OptimizeTarget.COST
    assert _parse_optimize_target("time") == OptimizeTarget.TIME


def test_parse_optimize_target_invalid():
    with pytest.raises(ValueError, match="Invalid optimize target"):
        _parse_optimize_target("INVALID")


# ---------------------------------------------------------------------------
# _parse_status_refresh_mode  (uses REAL sky.utils.common.StatusRefreshMode)
# ---------------------------------------------------------------------------


def test_parse_status_refresh_mode_all_values():
    assert _parse_status_refresh_mode("NONE") == StatusRefreshMode.NONE
    assert _parse_status_refresh_mode("AUTO") == StatusRefreshMode.AUTO
    assert _parse_status_refresh_mode("FORCE") == StatusRefreshMode.FORCE


def test_parse_status_refresh_mode_case_insensitive():
    assert _parse_status_refresh_mode("auto") == StatusRefreshMode.AUTO
    assert _parse_status_refresh_mode("force") == StatusRefreshMode.FORCE


def test_parse_status_refresh_mode_invalid():
    with pytest.raises(ValueError, match="Invalid refresh mode"):
        _parse_status_refresh_mode("INVALID")


# ---------------------------------------------------------------------------
# _parse_update_mode  (uses REAL sky.serve.serve_utils.UpdateMode)
# ---------------------------------------------------------------------------


def test_parse_update_mode_rolling():
    assert _parse_update_mode("rolling") == UpdateMode.ROLLING


def test_parse_update_mode_blue_green():
    assert _parse_update_mode("blue_green") == UpdateMode.BLUE_GREEN


def test_parse_update_mode_invalid():
    with pytest.raises(ValueError, match="Invalid update mode"):
        _parse_update_mode("invalid")


# ---------------------------------------------------------------------------
# capture_managed_job_logs
# ---------------------------------------------------------------------------


def test_capture_managed_job_logs_params(mock_sky):
    """Verify controller, refresh, task, tail params are forwarded."""

    def mock_tail_logs(**kwargs):
        kwargs["output_stream"].write("log line\n")
        return 0

    mock_sky.jobs.tail_logs.side_effect = mock_tail_logs

    result = capture_managed_job_logs(
        name="my-job",
        controller=True,
        refresh=True,
        task="task-0",
        tail=50,
    )
    assert "log line" in result
    kw = mock_sky.jobs.tail_logs.call_args[1]
    assert kw["controller"] is True
    assert kw["refresh"] is True
    assert kw["task"] == "task-0"
    assert kw["follow"] is False
    assert kw["tail"] == 50


def test_capture_managed_job_logs_nonzero_exit(mock_sky):
    mock_sky.jobs.tail_logs.side_effect = lambda **kw: 1
    with pytest.raises(RuntimeError, match="Failed to retrieve managed job logs"):
        capture_managed_job_logs(name="my-job")


def test_capture_managed_job_logs_tail_zero_becomes_none(mock_sky):
    """tail=0 should map to None (SDK convention for 'all lines')."""

    def mock_tail_logs(**kwargs):
        kwargs["output_stream"].write("all\n")
        return 0

    mock_sky.jobs.tail_logs.side_effect = mock_tail_logs
    capture_managed_job_logs(name="my-job", tail=0)
    assert mock_sky.jobs.tail_logs.call_args[1]["tail"] is None
