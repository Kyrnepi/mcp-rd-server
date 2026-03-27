"""Entry point for the Research & Desire Lockbox MCP server."""

import logging

import uvicorn

from src.auth import BearerAuthMiddleware
from src.config import config
from src.server import mcp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def create_app():
    """Build the ASGI application with authentication middleware."""
    config.validate()
    app = mcp.streamable_http_app()
    app.add_middleware(BearerAuthMiddleware)
    return app


app = create_app()

if __name__ == "__main__":
    logger.info(
        "Starting R&D Lockbox MCP server on %s:%s",
        config.RD_SERVER_HOST,
        config.RD_SERVER_PORT,
    )
    uvicorn.run(app, host=config.RD_SERVER_HOST, port=config.RD_SERVER_PORT)
