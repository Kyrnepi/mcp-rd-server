import json
import logging

from mcp.server.fastmcp import FastMCP

from src.rd_client import rd_client

logger = logging.getLogger(__name__)

mcp = FastMCP(
    "Research & Desire Lockbox",
    instructions=(
        "MCP server providing access to the Research & Desire Lockbox API. "
        "Manage lockbox devices, lock sessions, and lock templates."
    ),
    streamable_http_path="/mcp",
)


# ── Lockbox Devices ──────────────────────────────────────────────────────


@mcp.tool()
async def list_lockbox_devices(limit: int = 50, offset: int = 0) -> str:
    """List all Chastity Lockbox devices registered to your account, ordered by most recently visited.

    Args:
        limit: Number of records to return (1-100, default 50)
        offset: Number of records to skip (default 0)
    """
    result = await rd_client.list_lockbox_devices(limit=limit, offset=offset)
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_lockbox_device(device_id: int) -> str:
    """Get detailed information about a specific Chastity Lockbox device.

    Args:
        device_id: The lockbox device ID (minimum 1)
    """
    result = await rd_client.get_lockbox_device(device_id)
    return json.dumps(result, indent=2)


# ── Lock Sessions ────────────────────────────────────────────────────────


@mcp.tool()
async def list_lock_sessions(limit: int = 50, offset: int = 0) -> str:
    """List all lock sessions with segment history, ordered by most recent first.

    Args:
        limit: Number of records to return (1-100, default 50)
        offset: Number of records to skip (default 0)
    """
    result = await rd_client.list_lock_sessions(limit=limit, offset=offset)
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_lock_session(session_id: int) -> str:
    """Get detailed information about a specific lock session, including all segment history.

    Args:
        session_id: The lock session ID (minimum 1)
    """
    result = await rd_client.get_lock_session(session_id)
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_active_lock_session() -> str:
    """Get the currently active lock session for your account, including segment history.
    Returns null in the data field if no session is active."""
    result = await rd_client.get_active_lock_session()
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_latest_lock_session() -> str:
    """Get the most recent lock session with all segment history.
    Returns null if no sessions exist."""
    result = await rd_client.get_latest_lock_session()
    return json.dumps(result, indent=2)


@mcp.tool()
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
    result = await rd_client.lock_or_unlock(
        action=action,
        lock_settings_id=lock_settings_id,
        keyholder_ids=keyholder_ids,
        target_user_id=target_user_id,
        is_test_lock=is_test_lock,
    )
    return json.dumps(result, indent=2)


@mcp.tool()
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
    result = await rd_client.modify_active_lock_session(
        duration=duration,
        target_user_id=target_user_id,
    )
    return json.dumps(result, indent=2)


# ── Lock Templates ───────────────────────────────────────────────────────


@mcp.tool()
async def list_lock_templates(limit: int = 50, offset: int = 0) -> str:
    """List all lock templates you have access to.

    Args:
        limit: Number of records to return (1-100, default 50)
        offset: Number of records to skip (default 0)
    """
    result = await rd_client.list_lock_templates(limit=limit, offset=offset)
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_lock_template(template_id: int) -> str:
    """Get detailed information about a specific lock template.

    Args:
        template_id: The lock template ID (minimum 1)
    """
    result = await rd_client.get_lock_template(template_id)
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_active_lock_template() -> str:
    """Get the lock template used by the current active lock session.
    Returns null if there is no active lock."""
    result = await rd_client.get_active_lock_template()
    return json.dumps(result, indent=2)
