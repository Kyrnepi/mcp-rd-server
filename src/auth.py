import json
import logging

from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send

from src.config import config

logger = logging.getLogger(__name__)


def _json_rpc_error(code: int, message: str, status_code: int) -> Response:
    """Build a JSON-RPC error response."""
    return Response(
        content=json.dumps(
            {
                "jsonrpc": "2.0",
                "error": {"code": code, "message": message},
                "id": None,
            }
        ),
        status_code=status_code,
        media_type="application/json",
    )


class RateLimitMiddleware:
    """Simple in-memory rate limiter per client IP.

    Allows MCP_RATE_LIMIT requests per MCP_RATE_LIMIT_WINDOW seconds.
    """

    def __init__(self, app: ASGIApp):
        self.app = app
        self._buckets: dict[str, list[float]] = {}

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http":
            import time

            client_host = scope.get("client", ("unknown",))[0]
            now = time.monotonic()
            window = config.MCP_RATE_LIMIT_WINDOW

            bucket = self._buckets.setdefault(client_host, [])
            # Evict expired entries
            bucket[:] = [t for t in bucket if now - t < window]

            if len(bucket) >= config.MCP_RATE_LIMIT:
                logger.warning("Rate limit exceeded for %s", client_host)
                response = _json_rpc_error(
                    -32000, "Too many requests", 429
                )
                await response(scope, receive, send)
                return

            bucket.append(now)

        await self.app(scope, receive, send)


class BearerAuthMiddleware:
    """ASGI middleware that enforces Bearer token authentication on HTTP requests."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] in ("http", "websocket"):
            # Skip auth if no token is configured
            if not config.MCP_AUTH_TOKEN:
                await self.app(scope, receive, send)
                return

            # Extract Authorization header
            headers = dict(scope.get("headers", []))
            auth_header = headers.get(b"authorization", b"").decode()

            if (
                not auth_header.startswith("Bearer ")
                or auth_header[7:] != config.MCP_AUTH_TOKEN
            ):
                client_host = scope.get("client", ("unknown",))[0]
                logger.warning("Unauthorized MCP request from %s", client_host)
                response = _json_rpc_error(
                    -32000,
                    "Unauthorized: invalid or missing bearer token",
                    401,
                )
                await response(scope, receive, send)
                return

        await self.app(scope, receive, send)
