# skypilot-mcp

MCP server for [SkyPilot](https://github.com/skypilot-org/skypilot). Lets LLMs manage cloud clusters, jobs, and storage through the [Model Context Protocol](https://modelcontextprotocol.io/).

Built with [fastmcp](https://github.com/jlowin/fastmcp) v3.

## Demo

https://github.com/user-attachments/assets/ce90b863-b186-4673-a247-63fb84483a35

## Setup

Requires Python 3.10+.

```bash
# Claude Code
claude mcp add --transport stdio --scope project skypilot -- \
  uvx --from git+https://github.com/alex000kim/skypilot-mcp skypilot-mcp

# With a remote SkyPilot API server
claude mcp add --transport stdio --scope project \
  --env SKYPILOT_API_SERVER_ENDPOINT=http://your-server:46580 \
  skypilot -- \
  uvx --from git+https://github.com/alex000kim/skypilot-mcp skypilot-mcp
```

For Claude Desktop, add to your MCP config:

```json
{
  "mcpServers": {
    "skypilot": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/alex000kim/skypilot-mcp", "skypilot-mcp"]
    }
  }
}
```

## Using in your own repos

This repo includes a [`.mcp.json`](.mcp.json) file. Copy it into any repo that contains SkyPilot task YAMLs, and coding agents (Claude Code, Cursor, Windsurf, etc.) working in that repo will automatically have access to all SkyPilot MCP tools — launching clusters, submitting jobs, checking status, and more — without any manual setup.

```bash
cp .mcp.json /path/to/your-skypilot-project/
```

## Tools

### Clusters

| Tool | Description |
|------|-------------|
| `skypilot_cluster_status` | List clusters and their statuses |
| `skypilot_cluster_launch` | Launch a cluster from a task YAML |
| `skypilot_cluster_exec` | Run a task on an existing cluster |
| `skypilot_cluster_stop` | Stop a cluster (preserves disk) |
| `skypilot_cluster_start` | Restart a stopped cluster |
| `skypilot_cluster_down` | Tear down a cluster |
| `skypilot_cluster_autostop` | Set idle autostop timer |
| `skypilot_cluster_endpoints` | Get cluster endpoint URLs |

### Jobs (on a cluster)

| Tool | Description |
|------|-------------|
| `skypilot_job_queue` | List jobs on a cluster |
| `skypilot_job_status` | Get status of specific jobs |
| `skypilot_job_cancel` | Cancel jobs |
| `skypilot_job_logs` | Get job log snapshot (last N lines) |

### Managed Jobs (auto-recovery, spot)

| Tool | Description |
|------|-------------|
| `skypilot_managed_job_launch` | Launch a managed job |
| `skypilot_managed_job_queue` | List managed jobs (with sorting/pagination) |
| `skypilot_managed_job_cancel` | Cancel managed jobs |
| `skypilot_managed_job_logs` | Get managed job log snapshot |

### Worker Pools

| Tool | Description |
|------|-------------|
| `skypilot_pool_apply` | Create or update a worker pool |
| `skypilot_pool_status` | Get pool statuses |
| `skypilot_pool_down` | Delete worker pool(s) |
| `skypilot_pool_logs` | Get pool log snapshot |

### Services (Sky Serve)

| Tool | Description |
|------|-------------|
| `skypilot_serve_up` | Launch a service |
| `skypilot_serve_update` | Update service config (rolling/blue-green) |
| `skypilot_serve_down` | Tear down service(s) |
| `skypilot_serve_status` | Get service statuses |
| `skypilot_serve_logs` | Get service log snapshot |
| `skypilot_serve_terminate_replica` | Terminate a specific replica |

### Volumes

| Tool | Description |
|------|-------------|
| `skypilot_volume_apply` | Create or register a volume (PVC, RunPod) |
| `skypilot_volume_ls` | List volumes |
| `skypilot_volume_delete` | Delete volumes |

### DAG Optimization & Validation

| Tool | Description |
|------|-------------|
| `skypilot_optimize` | Find best cloud/region/instance for a task |
| `skypilot_validate` | Validate a task config without launching |

### Log Downloads

| Tool | Description |
|------|-------------|
| `skypilot_download_logs` | Download cluster job logs locally |
| `skypilot_managed_job_download_logs` | Download managed job logs |
| `skypilot_serve_download_logs` | Download service logs |
| `skypilot_pool_download_logs` | Download pool logs |
| `skypilot_tail_provision_logs` | Get cluster provisioning logs |
| `skypilot_tail_autostop_logs` | Get cluster autostop hook logs |

### Infrastructure

| Tool | Description |
|------|-------------|
| `skypilot_check` | Verify cloud credentials |
| `skypilot_enabled_clouds` | List enabled clouds |
| `skypilot_list_accelerators` | List available GPUs/TPUs |
| `skypilot_list_accelerator_counts` | List accelerator availability counts |
| `skypilot_kubernetes_node_info` | Get K8s node resources |
| `skypilot_realtime_gpu_availability` | Real-time K8s GPU availability |
| `skypilot_kubernetes_label_gpus` | Label K8s GPU nodes for SkyPilot |
| `skypilot_status_kubernetes` | Get all SkyPilot resources in K8s |
| `skypilot_local_up` / `_down` | Manage local K8s cluster |
| `skypilot_ssh_up` / `_down` | Manage SSH node pools |
| `skypilot_realtime_slurm_gpu_availability` | Real-time Slurm GPU availability |
| `skypilot_slurm_node_info` | Get Slurm node resources |

### Storage & Cost

| Tool | Description |
|------|-------------|
| `skypilot_storage_ls` | List storage objects |
| `skypilot_storage_delete` | Delete a storage object |
| `skypilot_cost_report` | Get cluster cost reports |

### API Server

| Tool | Description |
|------|-------------|
| `skypilot_api_info` | API server health and version |
| `skypilot_api_status` | List pending API requests |
| `skypilot_api_cancel` | Cancel API requests |
| `skypilot_get_request` | Wait for a request to complete |
| `skypilot_api_start` / `_stop` | Start or stop the API server |
| `skypilot_api_server_logs` | Get API server logs |
| `skypilot_api_login` / `_logout` | Authenticate with remote API server |

### Config & Utilities

| Tool | Description |
|------|-------------|
| `skypilot_reload_config` | Reload `~/.sky/config.yaml` |
| `skypilot_workspaces` | List workspaces |
| `skypilot_dashboard` | Open SkyPilot dashboard |
| `skypilot_jobs_dashboard` | Open managed jobs dashboard |

## How it works

Long-running operations (`launch`, `exec`, `stop`, `down`, `start`, etc.) return a `request_id` immediately. Use `skypilot_get_request` with that ID to poll for the result. Read-only operations like `status`, `queue`, and `cost_report` block and return results directly.

The server uses SkyPilot's sync Python SDK. fastmcp runs sync tools in a threadpool, so nothing blocks the event loop.

## API server configuration

The MCP server connects to whatever SkyPilot API server your environment is configured for:

- **Local (default)**: SkyPilot auto-starts a local API server on first use
- **Remote**: Set `SKYPILOT_API_SERVER_ENDPOINT` env var or configure `~/.sky/config.yaml`

## Development

```bash
git clone https://github.com/alex000kim/skypilot-mcp
cd skypilot-mcp
uv sync --extra dev
uv run pre-commit install
uv run pytest
```

Run the server locally:

```bash
# stdio (default)
uv run skypilot-mcp

# HTTP
uv run skypilot-mcp --transport http --port 8000
```
