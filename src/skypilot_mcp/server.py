"""SkyPilot MCP Server - entry point and tool registration."""

import argparse

from skypilot_mcp.app import mcp  # noqa: F401 — re-exported for backward compat

# Import tool modules to trigger @mcp.tool registration
from skypilot_mcp.tools import (  # noqa: E402, F401
    api_server,
    cluster,
    config,
    cost,
    dag,
    infra,
    jobs,
    logs,
    managed_jobs,
    pools,
    serve,
    storage,
    volumes,
)


def main():
    parser = argparse.ArgumentParser(description="SkyPilot MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http", "sse"],
        default="stdio",
        help="Transport protocol (default: stdio)",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host for http/sse")
    parser.add_argument("--port", type=int, default=8000, help="Port for http/sse")
    args = parser.parse_args()

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport=args.transport, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
