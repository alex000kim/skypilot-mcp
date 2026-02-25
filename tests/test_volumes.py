"""Tests for volume tools — config building and validation error handling."""

import pytest
from fastmcp.exceptions import ToolError
from unittest.mock import MagicMock, patch


def test_apply_builds_config_with_all_optional_params(mock_sky):
    """All optional params should be included in the config dict."""
    mock_volume = MagicMock()
    with patch(
        "sky.volumes.volume.Volume.from_yaml_config",
        return_value=mock_volume,
    ) as mock_from_yaml:
        from skypilot_mcp.tools.volumes import skypilot_volume_apply

        skypilot_volume_apply(
            name="v",
            volume_type="k8s-pvc",
            size="100GB",
            infra="k8s",
            labels={"env": "prod"},
            use_existing=True,
            config={"storage_class": "fast"},
        )

    config = mock_from_yaml.call_args[0][0]
    assert config["name"] == "v"
    assert config["type"] == "k8s-pvc"
    assert config["size"] == "100GB"
    assert config["infra"] == "k8s"
    assert config["labels"] == {"env": "prod"}
    assert config["use_existing"] is True
    assert config["config"] == {"storage_class": "fast"}


def test_apply_omits_none_optional_params(mock_sky):
    """None-valued optional params should not appear in the config dict."""
    mock_volume = MagicMock()
    with patch(
        "sky.volumes.volume.Volume.from_yaml_config",
        return_value=mock_volume,
    ) as mock_from_yaml:
        from skypilot_mcp.tools.volumes import skypilot_volume_apply

        skypilot_volume_apply(name="v", volume_type="k8s-pvc")

    config = mock_from_yaml.call_args[0][0]
    assert "size" not in config
    assert "infra" not in config
    assert "labels" not in config


def test_validate_error_raises_tool_error(mock_sky):
    mock_volume = MagicMock()
    mock_sky.volumes.validate.side_effect = ValueError("bad config")

    with patch(
        "sky.volumes.volume.Volume.from_yaml_config",
        return_value=mock_volume,
    ):
        from skypilot_mcp.tools.volumes import skypilot_volume_validate

        with pytest.raises(ToolError, match="Invalid input"):
            skypilot_volume_validate(name="v", volume_type="invalid")
