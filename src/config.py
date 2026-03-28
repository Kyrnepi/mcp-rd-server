import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def _parse_allowed_origins(raw: str) -> Optional[set[str]]:
    """Parse MCP_ALLOWED_ORIGINS env var.

    Returns None (allow all) when the value is empty or '*'.
    Otherwise returns a set of allowed origin strings.
    """
    raw = raw.strip()
    if not raw or raw == "*":
        return None
    return {o.strip() for o in raw.split(",") if o.strip()}


class Config:
    """Server configuration loaded from environment variables."""

    def __init__(self):
        # MCP server authentication token
        self.MCP_AUTH_TOKEN: str = os.environ.get("MCP_AUTH_TOKEN", "")

        # Research & Desire API settings
        self.RD_API_TOKEN: str = os.environ.get("RD_API_TOKEN", "")
        self.RD_API_BASE_URL: str = os.environ.get(
            "RD_API_BASE_URL",
            "https://dashboard.researchanddesire.com/api/v1",
        )
        self.RD_SERVER_PORT: int = int(os.environ.get("RD_SERVER_PORT", "3000"))
        self.RD_SERVER_HOST: str = os.environ.get("RD_SERVER_HOST", "0.0.0.0")

        # Origin validation (None = allow all, set = restrict)
        self.MCP_ALLOWED_ORIGINS: Optional[set[str]] = _parse_allowed_origins(
            os.environ.get("MCP_ALLOWED_ORIGINS", "*")
        )

        # Rate limiting
        self.MCP_RATE_LIMIT: int = int(os.environ.get("MCP_RATE_LIMIT", "100"))
        self.MCP_RATE_LIMIT_WINDOW: int = int(
            os.environ.get("MCP_RATE_LIMIT_WINDOW", "60")
        )

    def validate(self):
        """Log warnings for missing critical configuration."""
        if not self.RD_API_TOKEN:
            logger.warning("RD_API_TOKEN is not set — R&D API calls will fail")
        if not self.MCP_AUTH_TOKEN:
            logger.warning(
                "MCP_AUTH_TOKEN is not set — MCP server is running WITHOUT authentication"
            )


config = Config()
