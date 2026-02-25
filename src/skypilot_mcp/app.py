"""FastMCP application instance.

Separated from server.py so tool modules can import `mcp` without
creating a circular dependency (server.py imports tools, tools import mcp).
"""

import asyncio

import sky
from fastmcp import FastMCP
from fastmcp.server.lifespan import lifespan


@lifespan
async def skypilot_lifespan(server):
    """Verify SkyPilot API server connectivity at startup."""
    try:
        # Run the blocking SDK call in a thread to avoid blocking the
        # async event loop during startup.
        await asyncio.to_thread(sky.api_info)
        yield {}
    except Exception:
        # Allow server to start even if SkyPilot API is not yet running.
        # SkyPilot auto-starts its local API server on first SDK call.
        yield {}


_TASK_YAML_REFERENCE = """\

## Task YAML Format Reference

Tools that accept a `task_yaml` parameter expect a SkyPilot task YAML string.

### Top-level fields (all optional)

- `name` — Task name
- `resources` — Compute requirements (see below)
- `num_nodes` — Number of nodes (for distributed tasks)
- `setup` — Shell commands run once during provisioning
- `run` — Shell commands run as the task
- `envs` — Environment variables (`KEY: value`)
- `file_mounts` — Mount local files/dirs or cloud storage to remote paths
- `workdir` — Local directory to sync to the cluster
- `service` — SkyServe service config (mutually exclusive with `pool`)
- `pool` — Worker pool config (mutually exclusive with `service`)

### Resources section

```yaml
resources:
  infra: <target>               # Where to run (see infra syntax below)
  cpus: 2+                      # CPU count ("+" means at least)
  memory: 8+                    # Memory in GiB
  accelerators: A100:1          # GPU/TPU type and count
  instance_type: p3.2xlarge     # Specific instance type (optional)
  disk_size: 256                # Disk size in GiB
  disk_tier: best               # low | medium | high | best
  use_spot: false               # Use spot/preemptible instances
  ports:
    - 8888                      # Ports to expose
  image_id: skypilot:gpu-ubuntu-2204  # OS image (optional)
  labels:                       # Instance labels/tags (optional)
    team: ml
```

### Infra field syntax (targeting specific clouds/k8s/ssh)

IMPORTANT: Use `resources.infra` with forward-slash separators. Do NOT use \
nested YAML objects or colons for infrastructure targeting.

Format: `<cloud>[/<region>[/<zone>]]`

Examples:
- `aws` — Any AWS region
- `aws/us-east-1` — Specific AWS region
- `aws/us-east-1/us-east-1a` — Specific zone
- `gcp/us-central1` — Specific GCP region
- `kubernetes` — Default Kubernetes context
- `kubernetes/<context-name>` — Specific Kubernetes context
- `k8s/<context-name>` — Same (k8s is alias for kubernetes)

If omitted, SkyPilot auto-selects the cheapest option.

### Service section (for sky serve)

```yaml
service:
  replicas: 2                        # Fixed replica count
  readiness_probe:
    path: /health                    # Health-check endpoint
    initial_delay_seconds: 300       # Delay before first probe
  # Or for autoscaling:
  replica_policy:
    min_replicas: 1
    max_replicas: 10
    target_qps_per_replica: 10
```

### Pool section (for worker pools)

```yaml
pool:
  workers: 4          # Static worker count
  # Or for autoscaling:
  # min_workers: 1
  # max_workers: 10
  # queue_length_threshold: 5
```

### Job groups (multi-document YAML for parallel tasks)

Separate tasks with `---`. Each task has its own resources/setup/run:

```yaml
name: my-pipeline
---
name: train
resources:
  accelerators: V100:1
run: python train.py
---
name: eval
resources:
  accelerators: T4:1
run: python eval.py
```

### Accelerator format

String: `"V100"`, `"V100:2"`, `"A100:4"`, `"L4:1"`, `"H100:8"`
Dict: `{V100: 2}`
List (any-of): `["V100:1", "A100:1"]`

### File mounts

```yaml
file_mounts:
  /remote/path: /local/path          # Local file or directory
  /data:
    name: my-bucket                   # Cloud storage bucket
    mode: MOUNT                       # MOUNT or COPY
```

### Kubernetes and ports

On Kubernetes, `ports` requires ingress or load-balancer support, which not \
all clusters have. If a launch fails with a ports-related RBAC error (e.g., \
cannot list `ingressclasses`), retry without `ports` and tell the user to \
access the service via SSH port forwarding instead: \
`ssh <cluster_name> -L <port>:localhost:<port>`

### Complete examples

Cluster with Jupyter on Kubernetes (no `ports` — use SSH forwarding):
```yaml
resources:
  infra: kubernetes/my-context
  cpus: 2+
  memory: 4+
setup: pip install jupyter
run: jupyter notebook --no-browser --port=8888 --ip=0.0.0.0 \
  --NotebookApp.token='' --NotebookApp.password=''
```

GPU training on AWS:
```yaml
resources:
  infra: aws/us-east-1
  accelerators: A100:1
  disk_size: 500
setup: pip install torch
run: python train.py --epochs 100
```
"""

mcp = FastMCP(
    "skypilot-mcp",
    instructions=(
        "SkyPilot MCP server for managing cloud clusters, jobs, and resources. "
        "Long-running operations (launch, exec, stop, down, start) return a "
        "request_id. Use skypilot_get_request to poll for their results."
        + _TASK_YAML_REFERENCE
    ),
    lifespan=skypilot_lifespan,
)
