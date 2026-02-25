"""Volume management tools."""

import json

import sky

from skypilot_mcp.app import mcp
from skypilot_mcp.helpers import (
    handle_skypilot_error,
    resolve_request,
    safe_json_serialize,
)


@mcp.tool(
    name="skypilot_volume_apply",
    description=(
        "Create or register a volume. Accepts a volume configuration as a "
        "JSON/dict with fields: name, type ('k8s-pvc' or 'runpod-network-volume'), "
        "size (e.g. '100GB'), and optional fields like infra, labels, "
        "use_existing, config. Returns a request_id."
    ),
    tags={"volume"},
    annotations={"destructiveHint": False, "openWorldHint": True},
)
@handle_skypilot_error
def skypilot_volume_apply(
    name: str,
    volume_type: str,
    size: str | None = None,
    infra: str | None = None,
    labels: dict[str, str] | None = None,
    use_existing: bool | None = None,
    config: dict | None = None,
) -> str:
    """Create or register a volume."""
    from sky.volumes.volume import Volume

    vol_config: dict = {
        "name": name,
        "type": volume_type,
    }
    if size is not None:
        vol_config["size"] = size
    if infra is not None:
        vol_config["infra"] = infra
    if labels is not None:
        vol_config["labels"] = labels
    if use_existing is not None:
        vol_config["use_existing"] = use_existing
    if config is not None:
        vol_config["config"] = config

    volume = Volume.from_yaml_config(vol_config)
    request_id = sky.volumes.apply(volume)
    return json.dumps(
        {
            "request_id": str(request_id),
            "name": name,
            "message": "Volume apply request submitted.",
        }
    )


@mcp.tool(
    name="skypilot_volume_ls",
    description=(
        "List all volumes. Set refresh=True to refresh volume state from "
        "cloud APIs before returning (slower but most up-to-date)."
    ),
    tags={"volume"},
    annotations={"readOnlyHint": True},
)
@handle_skypilot_error
def skypilot_volume_ls(
    refresh: bool = False,
) -> str:
    """List volumes."""
    request_id = sky.volumes.ls(refresh=refresh)
    result = resolve_request(request_id)
    return safe_json_serialize(result)


@mcp.tool(
    name="skypilot_volume_delete",
    description=(
        "Delete one or more volumes by name. Set purge=True to force "
        "deletion from the database even if the cloud deletion fails. "
        "Returns a request_id."
    ),
    tags={"volume"},
    annotations={"destructiveHint": True},
)
@handle_skypilot_error
def skypilot_volume_delete(
    names: list[str],
    purge: bool = False,
) -> str:
    """Delete volumes."""
    request_id = sky.volumes.delete(names=names, purge=purge)
    return json.dumps(
        {
            "request_id": str(request_id),
            "names": names,
            "message": "Volume delete request submitted.",
        }
    )


@mcp.tool(
    name="skypilot_volume_validate",
    description=(
        "Validate a volume configuration without creating it. "
        "Checks that the volume specification is valid on the server side. "
        "Raises an error if validation fails, returns success otherwise."
    ),
    tags={"volume"},
    annotations={"readOnlyHint": True},
)
@handle_skypilot_error
def skypilot_volume_validate(
    name: str,
    volume_type: str,
    size: str | None = None,
    infra: str | None = None,
    labels: dict[str, str] | None = None,
    use_existing: bool | None = None,
    config: dict | None = None,
) -> str:
    """Validate a volume configuration."""
    from sky.volumes.volume import Volume

    vol_config: dict = {
        "name": name,
        "type": volume_type,
    }
    if size is not None:
        vol_config["size"] = size
    if infra is not None:
        vol_config["infra"] = infra
    if labels is not None:
        vol_config["labels"] = labels
    if use_existing is not None:
        vol_config["use_existing"] = use_existing
    if config is not None:
        vol_config["config"] = config

    volume = Volume.from_yaml_config(vol_config)
    sky.volumes.validate(volume)
    return json.dumps(
        {
            "status": "valid",
            "name": name,
            "message": "Volume validation passed.",
        }
    )
