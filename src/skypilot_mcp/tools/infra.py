"""Infrastructure and cloud resource tools."""

import json

import sky

from skypilot_mcp.app import mcp
from skypilot_mcp.helpers import (
    handle_skypilot_error,
    resolve_request,
    safe_json_serialize,
)


@mcp.tool(
    name="skypilot_check",
    description=(
        "Check and enable infrastructure credentials. Verifies that credentials "
        "are configured correctly for the specified infrastructure (clouds, "
        "Kubernetes, SSH, Slurm). If no infra specified, checks all supported "
        "infrastructure. Optionally specify a workspace name to scope the "
        "check to a specific workspace."
    ),
    tags={"infra"},
    annotations={"readOnlyHint": True},
)
@handle_skypilot_error
def skypilot_check(
    infra: list[str] | None = None,
    verbose: bool = False,
    workspace: str | None = None,
) -> str:
    """Check infrastructure credentials."""
    infra_tuple = tuple(infra) if infra is not None else None
    request_id = sky.check(infra_list=infra_tuple, verbose=verbose, workspace=workspace)
    result = resolve_request(request_id)
    return safe_json_serialize(result)


@mcp.tool(
    name="skypilot_enabled_clouds",
    description=(
        "List all clouds that have been enabled (credentials configured). "
        "Returns a list of cloud names. Set expand=True to expand Kubernetes "
        "and SSH into individual resource pools. Optionally specify a workspace "
        "name to scope the listing to a specific workspace."
    ),
    tags={"infra"},
    annotations={"readOnlyHint": True},
)
@handle_skypilot_error
def skypilot_enabled_clouds(
    expand: bool = False,
    workspace: str | None = None,
) -> str:
    """Get enabled clouds."""
    request_id = sky.enabled_clouds(expand=expand, workspace=workspace)
    result = resolve_request(request_id)
    return safe_json_serialize(result)


@mcp.tool(
    name="skypilot_list_accelerators",
    description=(
        "List available accelerators (GPUs/TPUs) across clouds. "
        "Filter by name, region, quantity, or specific clouds. "
        "Set gpus_only=False to include non-GPU accelerators like TPUs. "
        "Set case_sensitive=False for case-insensitive name filtering."
    ),
    tags={"infra"},
    annotations={"readOnlyHint": True},
)
@handle_skypilot_error
def skypilot_list_accelerators(
    gpus_only: bool = True,
    name_filter: str | None = None,
    region_filter: str | None = None,
    quantity_filter: int | None = None,
    clouds: list[str] | None = None,
    all_regions: bool = False,
    require_price: bool = True,
    case_sensitive: bool = True,
) -> str:
    """List available accelerators."""
    request_id = sky.list_accelerators(
        gpus_only=gpus_only,
        name_filter=name_filter,
        region_filter=region_filter,
        quantity_filter=quantity_filter,
        clouds=clouds,
        all_regions=all_regions,
        require_price=require_price,
        case_sensitive=case_sensitive,
    )
    result = resolve_request(request_id)
    return safe_json_serialize(result)


@mcp.tool(
    name="skypilot_list_accelerator_counts",
    description=(
        "List available accelerators and their available counts. "
        "Returns a mapping of accelerator names to available quantities. "
        "Filter by name, region, quantity, or specific clouds."
    ),
    tags={"infra"},
    annotations={"readOnlyHint": True},
)
@handle_skypilot_error
def skypilot_list_accelerator_counts(
    gpus_only: bool = True,
    name_filter: str | None = None,
    region_filter: str | None = None,
    quantity_filter: int | None = None,
    clouds: list[str] | None = None,
) -> str:
    """List available accelerator counts."""
    request_id = sky.list_accelerator_counts(
        gpus_only=gpus_only,
        name_filter=name_filter,
        region_filter=region_filter,
        quantity_filter=quantity_filter,
        clouds=clouds,
    )
    result = resolve_request(request_id)
    return safe_json_serialize(result)


@mcp.tool(
    name="skypilot_kubernetes_node_info",
    description=(
        "Get resource information for all nodes in a Kubernetes cluster. "
        "Shows CPU, memory, GPU, and other resource details per node."
    ),
    tags={"infra", "kubernetes"},
    annotations={"readOnlyHint": True},
)
@handle_skypilot_error
def skypilot_kubernetes_node_info(
    context: str | None = None,
) -> str:
    """Get Kubernetes node info."""
    request_id = sky.kubernetes_node_info(context=context)
    result = resolve_request(request_id)
    return safe_json_serialize(result)


@mcp.tool(
    name="skypilot_realtime_gpu_availability",
    description=(
        "Get real-time GPU availability in a Kubernetes cluster. "
        "Shows which GPUs are currently available and their quantities. "
        "Filter by GPU name or minimum quantity. "
        "Set is_ssh to filter by SSH-based (True) or Kubernetes-based (False) "
        "infrastructure, or leave unset for all."
    ),
    tags={"infra", "kubernetes"},
    annotations={"readOnlyHint": True},
)
@handle_skypilot_error
def skypilot_realtime_gpu_availability(
    context: str | None = None,
    name_filter: str | None = None,
    quantity_filter: int | None = None,
    is_ssh: bool | None = None,
) -> str:
    """Get real-time Kubernetes GPU availability."""
    request_id = sky.realtime_kubernetes_gpu_availability(
        context=context,
        name_filter=name_filter,
        quantity_filter=quantity_filter,
        is_ssh=is_ssh,
    )
    result = resolve_request(request_id)
    return safe_json_serialize(result)


@mcp.tool(
    name="skypilot_kubernetes_label_gpus",
    description=(
        "Label GPU nodes in a Kubernetes cluster for use with SkyPilot. "
        "Currently supports NVIDIA GPUs only. Set cleanup_only=True to "
        "remove existing labeling resources. Returns a request_id."
    ),
    tags={"infra", "kubernetes"},
    annotations={"destructiveHint": False},
)
@handle_skypilot_error
def skypilot_kubernetes_label_gpus(
    context: str | None = None,
    cleanup_only: bool = False,
    wait_for_completion: bool = True,
) -> str:
    """Label Kubernetes GPU nodes."""
    request_id = sky.kubernetes_label_gpus(
        context=context,
        cleanup_only=cleanup_only,
        wait_for_completion=wait_for_completion,
    )
    return json.dumps(
        {
            "request_id": str(request_id),
            "message": "Kubernetes GPU labeling request submitted.",
        }
    )


@mcp.tool(
    name="skypilot_status_kubernetes",
    description=(
        "[Experimental] Get all SkyPilot clusters and jobs in a Kubernetes "
        "cluster. Includes managed jobs and services. Returns cluster info, "
        "managed job records, and context information."
    ),
    tags={"infra", "kubernetes"},
    annotations={"readOnlyHint": True},
)
@handle_skypilot_error
def skypilot_status_kubernetes() -> str:
    """Get Kubernetes cluster status."""
    request_id = sky.status_kubernetes()
    result = resolve_request(request_id)
    # Unpack defensively in case the return format changes.
    if isinstance(result, (list, tuple)) and len(result) >= 4:
        clusters, other_clusters, managed_jobs, context = (
            result[0],
            result[1],
            result[2],
            result[3],
        )
        return safe_json_serialize(
            {
                "clusters": clusters,
                "other_clusters": other_clusters,
                "managed_jobs": managed_jobs,
                "context": context,
            }
        )
    return safe_json_serialize(result)


@mcp.tool(
    name="skypilot_local_up",
    description=(
        "Launch a local Kubernetes cluster for SkyPilot. "
        "Set gpus=True to enable GPU passthrough. "
        "Only works when the API server is running locally. Returns a request_id."
    ),
    tags={"infra", "local"},
    annotations={"destructiveHint": False, "openWorldHint": True},
)
@handle_skypilot_error
def skypilot_local_up(
    gpus: bool = False,
    name: str | None = None,
    port_start: int | None = None,
) -> str:
    """Launch a local Kubernetes cluster."""
    request_id = sky.local_up(gpus=gpus, name=name, port_start=port_start)
    return json.dumps(
        {
            "request_id": str(request_id),
            "message": "Local cluster launch submitted.",
        }
    )


@mcp.tool(
    name="skypilot_local_down",
    description=(
        "Tear down the local Kubernetes cluster started by local_up. "
        "Only works when the API server is running locally. Returns a request_id."
    ),
    tags={"infra", "local"},
    annotations={"destructiveHint": True},
)
@handle_skypilot_error
def skypilot_local_down(
    name: str | None = None,
) -> str:
    """Tear down a local Kubernetes cluster."""
    request_id = sky.local_down(name=name)
    return json.dumps(
        {
            "request_id": str(request_id),
            "message": "Local cluster teardown submitted.",
        }
    )


@mcp.tool(
    name="skypilot_ssh_up",
    description=(
        "Deploy SSH node pools defined in ~/.sky/ssh_node_pools.yaml. "
        "Optionally specify a specific infra name or config file path. "
        "Returns a request_id."
    ),
    tags={"infra", "ssh"},
    annotations={"destructiveHint": False, "openWorldHint": True},
)
@handle_skypilot_error
def skypilot_ssh_up(
    infra: str | None = None,
    file: str | None = None,
) -> str:
    """Deploy SSH node pools."""
    request_id = sky.ssh_up(infra=infra, file=file)
    return json.dumps(
        {
            "request_id": str(request_id),
            "message": "SSH node pool deployment submitted.",
        }
    )


@mcp.tool(
    name="skypilot_ssh_down",
    description=(
        "Tear down Kubernetes cluster on SSH targets. "
        "Optionally specify a specific infra name. Returns a request_id."
    ),
    tags={"infra", "ssh"},
    annotations={"destructiveHint": True},
)
@handle_skypilot_error
def skypilot_ssh_down(
    infra: str | None = None,
) -> str:
    """Tear down SSH node pools."""
    request_id = sky.ssh_down(infra=infra)
    return json.dumps(
        {
            "request_id": str(request_id),
            "message": "SSH node pool teardown submitted.",
        }
    )


@mcp.tool(
    name="skypilot_realtime_slurm_gpu_availability",
    description=(
        "Get real-time GPU availability in a Slurm cluster. "
        "Shows which GPUs are currently available and their quantities. "
        "Filter by GPU name, minimum quantity, or Slurm cluster name."
    ),
    tags={"infra", "slurm"},
    annotations={"readOnlyHint": True},
)
@handle_skypilot_error
def skypilot_realtime_slurm_gpu_availability(
    name_filter: str | None = None,
    quantity_filter: int | None = None,
    slurm_cluster_name: str | None = None,
) -> str:
    """Get real-time Slurm GPU availability."""
    request_id = sky.realtime_slurm_gpu_availability(
        name_filter=name_filter,
        quantity_filter=quantity_filter,
        slurm_cluster_name=slurm_cluster_name,
    )
    result = resolve_request(request_id)
    return safe_json_serialize(result)


@mcp.tool(
    name="skypilot_slurm_node_info",
    description=(
        "Get resource information for all nodes in a Slurm cluster. "
        "Shows node name, partition, state, GPU type, total/free GPUs, "
        "vCPU count, and memory."
    ),
    tags={"infra", "slurm"},
    annotations={"readOnlyHint": True},
)
@handle_skypilot_error
def skypilot_slurm_node_info(
    slurm_cluster_name: str | None = None,
) -> str:
    """Get Slurm node info."""
    request_id = sky.slurm_node_info(slurm_cluster_name=slurm_cluster_name)
    result = resolve_request(request_id)
    return safe_json_serialize(result)
