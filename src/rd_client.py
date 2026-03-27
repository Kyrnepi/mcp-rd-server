import logging
from typing import Any, Optional

import httpx

from src.config import config

logger = logging.getLogger(__name__)


class RDClient:
    """Async HTTP client for the Research & Desire API."""

    def __init__(self):
        self.base_url = config.RD_API_BASE_URL.rstrip("/")
        self.token = config.RD_API_TOKEN

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[dict] = None,
        json_body: Optional[dict] = None,
    ) -> dict[str, Any]:
        """Execute an HTTP request against the R&D API."""
        url = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self._headers(),
                    params=params,
                    json=json_body,
                    timeout=30.0,
                )
                if response.status_code >= 400:
                    try:
                        body = response.json()
                    except Exception:
                        body = {"error": response.text}
                    return {"ok": False, "status_code": response.status_code, **body}
                return response.json()
        except httpx.TimeoutException:
            logger.error("Timeout calling %s %s", method, url)
            return {"ok": False, "error": f"Request to {url} timed out"}
        except httpx.ConnectError:
            logger.error("Connection failed for %s %s", method, url)
            return {"ok": False, "error": f"Failed to connect to {url}"}
        except Exception as exc:
            logger.error("Unexpected error calling %s %s: %s", method, url, exc)
            return {"ok": False, "error": str(exc)}

    # ── Lockbox Devices ──────────────────────────────────────────────

    async def list_lockbox_devices(
        self, limit: int = 50, offset: int = 0
    ) -> dict[str, Any]:
        """Returns all Chastity Lockbox devices registered to the account."""
        return await self._request(
            "GET", "/lkbx", params={"limit": limit, "offset": offset}
        )

    async def get_lockbox_device(self, device_id: int) -> dict[str, Any]:
        """Returns detailed information about a specific Lockbox device."""
        return await self._request("GET", f"/lkbx/{device_id}")

    # ── Lock Sessions ────────────────────────────────────────────────

    async def list_lock_sessions(
        self, limit: int = 50, offset: int = 0
    ) -> dict[str, Any]:
        """Returns all lock sessions with segment history."""
        return await self._request(
            "GET", "/lkbx/sessions", params={"limit": limit, "offset": offset}
        )

    async def get_lock_session(self, session_id: int) -> dict[str, Any]:
        """Returns detailed information about a specific lock session."""
        return await self._request("GET", f"/lkbx/sessions/{session_id}")

    async def get_active_lock_session(self) -> dict[str, Any]:
        """Returns the currently active lock session."""
        return await self._request("GET", "/lkbx/session/current")

    async def get_latest_lock_session(self) -> dict[str, Any]:
        """Returns the most recent lock session."""
        return await self._request("GET", "/lkbx/sessions/latest")

    async def lock_or_unlock(
        self,
        action: str,
        lock_settings_id: Optional[int] = None,
        keyholder_ids: Optional[list[int]] = None,
        target_user_id: Optional[int] = None,
        is_test_lock: Optional[bool] = None,
    ) -> dict[str, Any]:
        """Start a new lock session or complete the active session."""
        body: dict[str, Any] = {"action": action}
        if lock_settings_id is not None:
            body["lockSettingsId"] = lock_settings_id
        if keyholder_ids is not None:
            body["keyholderIds"] = keyholder_ids
        if target_user_id is not None:
            body["targetUserId"] = target_user_id
        if is_test_lock is not None:
            body["isTestLock"] = is_test_lock
        return await self._request("POST", "/lkbx/session/current", json_body=body)

    async def modify_active_lock_session(
        self,
        duration: int,
        target_user_id: Optional[int] = None,
    ) -> dict[str, Any]:
        """Modify the duration of an active lock session."""
        body: dict[str, Any] = {"duration": duration}
        if target_user_id is not None:
            body["targetUserId"] = target_user_id
        return await self._request("PATCH", "/lkbx/session/current", json_body=body)

    # ── Lock Templates ───────────────────────────────────────────────

    async def list_lock_templates(
        self, limit: int = 50, offset: int = 0
    ) -> dict[str, Any]:
        """Returns all lock templates the user has access to."""
        return await self._request(
            "GET", "/lkbx/templates", params={"limit": limit, "offset": offset}
        )

    async def get_lock_template(self, template_id: int) -> dict[str, Any]:
        """Returns detailed information about a specific lock template."""
        return await self._request("GET", f"/lkbx/templates/{template_id}")

    async def get_active_lock_template(self) -> dict[str, Any]:
        """Returns the lock template used by the current active lock session."""
        return await self._request("GET", "/lkbx/templates/active")


rd_client = RDClient()
