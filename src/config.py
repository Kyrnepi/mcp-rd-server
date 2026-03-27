import os
import logging

logger = logging.getLogger(__name__)


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

    def validate(self):
        """Log warnings for missing critical configuration."""
        if not self.RD_API_TOKEN:
            logger.warning("RD_API_TOKEN is not set — R&D API calls will fail")
        if not self.MCP_AUTH_TOKEN:
            logger.warning(
                "MCP_AUTH_TOKEN is not set — MCP server is running WITHOUT authentication"
            )


config = Config()
