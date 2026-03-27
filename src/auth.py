import json
import logging

from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send

from src.config import config

logger = logging.getLogger(__name__)


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
                response = Response(
                    content=json.dumps(
                        {
                            "jsonrpc": "2.0",
                            "error": {
                                "code": -32000,
                                "message": "Unauthorized: invalid or missing bearer token",
                            },
                            "id": None,
                        }
                    ),
                    status_code=401,
                    media_type="application/json",
                )
                await response(scope, receive, send)
                return

        await self.app(scope, receive, send)
