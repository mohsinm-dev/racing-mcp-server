"""
Racing API MCP Server — main entry point.

Supports two transport modes:
- stdio: for Claude Desktop (local use)
- sse: for HTTP/hosted deployments

Usage:
    # stdio mode (Claude Desktop)
    python -m racing_mcp.server

    # SSE/HTTP mode
    python -m racing_mcp.server --transport sse --host 0.0.0.0 --port 8080
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from typing import Any

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

from .client import get_racing_client
from .config import config
from .handlers import handle_tool
from .tools import TOOLS

# ── Logging setup ────────────────────────────────────────────────────────────────

_log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, _log_level, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],  # stderr so stdout stays clean for MCP
)
logger = logging.getLogger("racing_mcp.server")


# ── MCP Server ───────────────────────────────────────────────────────────────────

server = Server("racing-api-mcp")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """Return all available tools to Claude."""
    return TOOLS


@server.call_tool()
async def call_tool(
    name: str, arguments: dict[str, Any] | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Execute a tool call and return the result."""
    logger.info(f"Tool called: {name}")
    logger.debug(f"Tool args: {arguments}")

    args = arguments or {}

    try:
        result = await handle_tool(name, args)

        # Format result as pretty JSON
        result_text = json.dumps(result, indent=2, ensure_ascii=False)

        return [types.TextContent(type="text", text=result_text)]

    except PermissionError as e:
        # Plan/auth issues — return a clear message rather than crashing
        error_msg = f"⚠️ Access Denied: {e}"
        logger.warning(error_msg)
        return [types.TextContent(type="text", text=error_msg)]

    except ValueError as e:
        error_msg = f"⚠️ Invalid Input: {e}"
        logger.warning(error_msg)
        return [types.TextContent(type="text", text=error_msg)]

    except Exception as e:
        error_msg = f"⚠️ Error calling {name}: {e}"
        logger.error(error_msg, exc_info=True)
        return [types.TextContent(type="text", text=error_msg)]


# ── Entry point ──────────────────────────────────────────────────────────────────

async def _run_stdio() -> None:
    """Run the MCP server in stdio mode (for Claude Desktop)."""
    config.validate()
    logger.info("Starting Racing API MCP Server in stdio mode...")

    try:
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="racing-api-mcp",
                    server_version="1.0.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
    finally:
        client = get_racing_client()
        await client.close()
        logger.info("Racing API client closed.")


async def _run_sse(host: str, port: int) -> None:
    """Run the MCP server in SSE/HTTP mode (for hosted deployments)."""
    config.validate()
    logger.info(f"Starting Racing API MCP Server in SSE mode on {host}:{port}")

    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.middleware import Middleware
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.routing import Mount, Route
    import uvicorn

    # Optional API key auth for SSE mode
    mcp_api_key = os.getenv("MCP_API_KEY")

    class APIKeyMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            if mcp_api_key:
                provided = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
                if provided != mcp_api_key:
                    return JSONResponse({"error": "Invalid or missing API key"}, status_code=401)
            return await call_next(request)

    sse = SseServerTransport("/messages")

    async def handle_health(request):
        return JSONResponse({"status": "ok"})

    async def handle_sse(request):
        async with sse.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await server.run(
                streams[0],
                streams[1],
                InitializationOptions(
                    server_name="racing-api-mcp",
                    server_version="1.0.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )

    async def handle_messages(request):
        await sse.handle_post_message(request.scope, request.receive, request._send)

    middleware = [Middleware(APIKeyMiddleware)] if mcp_api_key else []

    starlette_app = Starlette(
        routes=[
            Route("/health", endpoint=handle_health),
            Route("/sse", endpoint=handle_sse),
            Mount("/messages", app=handle_messages),
        ],
        middleware=middleware,
    )

    if mcp_api_key:
        logger.info("SSE mode: API key authentication enabled")
    else:
        logger.warning("SSE mode: No MCP_API_KEY set — running without authentication")

    uvicorn_config = uvicorn.Config(
        starlette_app,
        host=host,
        port=port,
        log_level="info",
    )
    uvicorn_server = uvicorn.Server(uvicorn_config)
    try:
        await uvicorn_server.serve()
    finally:
        client = get_racing_client()
        await client.close()
        logger.info("Racing API client closed.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Racing API MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport mode: stdio (for Claude Desktop) or sse (for HTTP hosting)",
    )
    parser.add_argument("--host", default=config.host, help="Host for SSE mode")
    parser.add_argument("--port", type=int, default=config.port, help="Port for SSE mode")
    args = parser.parse_args()

    if args.transport == "stdio":
        asyncio.run(_run_stdio())
    else:
        asyncio.run(_run_sse(args.host, args.port))


if __name__ == "__main__":
    main()
