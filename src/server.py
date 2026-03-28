import json
import logging

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations

from src.config import config
from src.rd_client import rd_client

logger = logging.getLogger(__name__)

mcp = FastMCP(
    "Research & Desire Lockbox",
    instructions=(
        "MCP server providing access to the Research & Desire Lockbox API. "
        "Manage lockbox devices, lock sessions, and lock templates."
    ),
    streamable_http_path="/mcp",
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=config.MCP_ALLOWED_ORIGINS is not None,
        allowed_hosts=list(config.MCP_ALLOWED_ORIGINS) if config.MCP_ALLOWED_ORIGINS else [],
        allowed_origins=list(config.MCP_ALLOWED_ORIGINS) if config.MCP_ALLOWED_ORIGINS else [],
    ),
)


# ── Helpers ─────────────────────────────────────────────────────────────


def _validate_limit_offset(limit: int, offset: int) -> None:
    """Validate common pagination parameters."""
    if limit < 1 or limit > 100:
        raise ToolError("limit must be between 1 and 100")
    if offset < 0:
        raise ToolError("offset must be >= 0")


def _validate_positive_id(value: int, name: str) -> None:
    """Validate that an ID is a positive integer."""
    if value < 1:
        raise ToolError(f"{name} must be >= 1")


async def _call(coro) -> str:
    """Await an rd_client coroutine and raise ToolError on API failure."""
    result = await coro
    if isinstance(result, dict) and result.get("ok") is False:
        raise ToolError(json.dumps(result, indent=2))
    return json.dumps(result, indent=2)


# ── Read-only annotations ──────────────────────────────────────────────

_READ_ONLY = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)

_MUTATING = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=True,
    idempotentHint=False,
    openWorldHint=False,
)

_MUTATING_IDEMPOTENT = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=True,
    idempotentHint=True,
    openWorldHint=False,
)


# ── Lockbox Devices ──────────────────────────────────────────────────────


@mcp.tool(title="List Lockbox Devices", annotations=_READ_ONLY)
async def list_lockbox_devices(limit: int = 50, offset: int = 0) -> str:
    """List all Chastity Lockbox devices registered to your account, ordered by most recently visited.

    Args:
        limit: Number of records to return (1-100, default 50)
        offset: Number of records to skip (default 0)
    """
    _validate_limit_offset(limit, offset)
    return await _call(rd_client.list_lockbox_devices(limit=limit, offset=offset))


@mcp.tool(title="Get Lockbox Device", annotations=_READ_ONLY)
async def get_lockbox_device(device_id: int) -> str:
    """Get detailed information about a specific Chastity Lockbox device.

    Args:
        device_id: The lockbox device ID (minimum 1)
    """
    _validate_positive_id(device_id, "device_id")
    return await _call(rd_client.get_lockbox_device(device_id))


# ── Lock Sessions ────────────────────────────────────────────────────────


@mcp.tool(title="List Lock Sessions", annotations=_READ_ONLY)
async def list_lock_sessions(limit: int = 50, offset: int = 0) -> str:
    """List all lock sessions with segment history, ordered by most recent first.

    Args:
        limit: Number of records to return (1-100, default 50)
        offset: Number of records to skip (default 0)
    """
    _validate_limit_offset(limit, offset)
    return await _call(rd_client.list_lock_sessions(limit=limit, offset=offset))


@mcp.tool(title="Get Lock Session", annotations=_READ_ONLY)
async def get_lock_session(session_id: int) -> str:
    """Get detailed information about a specific lock session, including all segment history.

    Args:
        session_id: The lock session ID (minimum 1)
    """
    _validate_positive_id(session_id, "session_id")
    return await _call(rd_client.get_lock_session(session_id))


@mcp.tool(title="Get Active Lock Session", annotations=_READ_ONLY)
async def get_active_lock_session() -> str:
    """Get the currently active lock session for your account, including segment history.
    Returns null in the data field if no session is active."""
    return await _call(rd_client.get_active_lock_session())


@mcp.tool(title="Get Latest Lock Session", annotations=_READ_ONLY)
async def get_latest_lock_session() -> str:
    """Get the most recent lock session with all segment history.
    Returns null if no sessions exist."""
    return await _call(rd_client.get_latest_lock_session())


@mcp.tool(title="Lock or Unlock", annotations=_MUTATING)
async def lock_or_unlock(
    action: str,
    lock_settings_id: int | None = None,
    keyholder_ids: list[int] | None = None,
    target_user_id: int | None = None,
    is_test_lock: bool | None = None,
) -> str:
    """Start a new lock session (lock) or complete the active session (unlock).

    User IDs (target and keyholders) are validated against your accessible users
    before the action is performed.

    Args:
        action: Must be "lock" or "unlock"
        lock_settings_id: Lock template ID — required when action is "lock"
        keyholder_ids: List of user IDs assigned as keyholders (for lock action)
        target_user_id: User ID to lock/unlock (defaults to the authenticated user)
        is_test_lock: When true, allows lock owner to self-unlock without keyholder
    """
    if action not in ("lock", "unlock"):
        raise ToolError('action must be "lock" or "unlock"')
    if action == "lock" and lock_settings_id is None:
        raise ToolError("lock_settings_id is required when action is 'lock'")
    if lock_settings_id is not None:
        _validate_positive_id(lock_settings_id, "lock_settings_id")
    if target_user_id is not None:
        _validate_positive_id(target_user_id, "target_user_id")
    if keyholder_ids is not None:
        for kid in keyholder_ids:
            _validate_positive_id(kid, "keyholder_ids entry")

    return await _call(
        rd_client.lock_or_unlock(
            action=action,
            lock_settings_id=lock_settings_id,
            keyholder_ids=keyholder_ids,
            target_user_id=target_user_id,
            is_test_lock=is_test_lock,
        )
    )


@mcp.tool(title="Modify Active Lock Session", annotations=_MUTATING_IDEMPOTENT)
async def modify_active_lock_session(
    duration: int,
    target_user_id: int | None = None,
) -> str:
    """Modify the duration of an active lock session.

    Only keyholders or test-lock owners can modify sessions.

    Args:
        duration: New session duration in seconds (minimum 1)
        target_user_id: User ID whose session to modify (defaults to the authenticated user)
    """
    if duration < 1:
        raise ToolError("duration must be >= 1")
    if target_user_id is not None:
        _validate_positive_id(target_user_id, "target_user_id")

    return await _call(
        rd_client.modify_active_lock_session(
            duration=duration,
            target_user_id=target_user_id,
        )
    )


# ── Lock Templates ───────────────────────────────────────────────────────


@mcp.tool(title="List Lock Templates", annotations=_READ_ONLY)
async def list_lock_templates(limit: int = 50, offset: int = 0) -> str:
    """List all lock templates you have access to.

    Args:
        limit: Number of records to return (1-100, default 50)
        offset: Number of records to skip (default 0)
    """
    _validate_limit_offset(limit, offset)
    return await _call(rd_client.list_lock_templates(limit=limit, offset=offset))


@mcp.tool(title="Get Lock Template", annotations=_READ_ONLY)
async def get_lock_template(template_id: int) -> str:
    """Get detailed information about a specific lock template.

    Args:
        template_id: The lock template ID (minimum 1)
    """
    _validate_positive_id(template_id, "template_id")
    return await _call(rd_client.get_lock_template(template_id))


@mcp.tool(title="Get Active Lock Template", annotations=_READ_ONLY)
async def get_active_lock_template() -> str:
    """Get the lock template used by the current active lock session.
    Returns null if there is no active lock."""
    return await _call(rd_client.get_active_lock_template())
