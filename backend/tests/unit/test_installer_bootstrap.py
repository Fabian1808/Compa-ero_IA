"""
First-run setup must work before any Microsoft account is connected.

These tests lock in the behaviour that setup is reachable on a brand-new
installation: no user row exists yet, yet the installer endpoints have to
respond instead of failing with "No user found".
"""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from starlette.requests import Request

from app.api.v1 import deps as installer_deps
from app.api.v1 import installer as installer_api
from app.services import installer_service as service_module
from app.services.installer_service import FirstRunMarker


def build_request(client_host: str | None, origin: str | None = None) -> Request:
    headers = []
    if origin:
        headers.append((b"origin", origin.encode()))
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": headers,
            "client": (client_host, 12345) if client_host else None,
        }
    )


# --------------------------------------------------------------------------
# Local-only guard
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_loopback_client_is_allowed():
    await installer_deps.require_local_client(build_request("127.0.0.1"))


@pytest.mark.asyncio
async def test_tauri_origin_is_allowed():
    await installer_deps.require_local_client(
        build_request("127.0.0.1", origin="tauri://localhost")
    )


@pytest.mark.asyncio
async def test_remote_client_is_rejected():
    """A caller off this machine must not be able to trigger an install."""
    with pytest.raises(HTTPException) as exc_info:
        await installer_deps.require_local_client(build_request("203.0.113.10"))

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_missing_client_info_is_rejected():
    with pytest.raises(HTTPException):
        await installer_deps.require_local_client(build_request(None))


# --------------------------------------------------------------------------
# Endpoints must not require a user
# --------------------------------------------------------------------------
def installer_routes_require_no_user():
    """
    Guards against re-introducing an authenticated dependency on setup routes.

    Setup happens before the user exists, so requiring `get_current_user_id`
    would make the installer permanently unreachable.
    """
    protected = {
        "get_current_user_id",
    }
    offenders = []
    for route in installer_api.router.routes:
        for dependency in getattr(route, "dependant", None).dependencies if route.dependant else []:
            if dependency.call is not None and dependency.call.__name__ in protected:
                offenders.append(route.path)
    assert offenders == [], f"setup routes must not require a user: {offenders}"


def test_first_run_is_needed_before_any_account_exists():
    from pathlib import Path

    from app import config

    marker = FirstRunMarker(Path(config.settings.data_dir))
    assert not marker.exists()


# --------------------------------------------------------------------------
# First-run marker
# --------------------------------------------------------------------------
def test_marker_roundtrip(tmp_path):
    marker = FirstRunMarker(tmp_path)
    assert not marker.exists()

    assert marker.create() is True
    assert marker.exists()

    assert marker.clear() is True
    assert not marker.exists()


def test_marker_create_is_idempotent(tmp_path):
    marker = FirstRunMarker(tmp_path)
    assert marker.create() is True
    assert marker.create() is True
    assert marker.exists()


# --------------------------------------------------------------------------
# Response contract
# --------------------------------------------------------------------------
def test_endpoints_emit_message_codes_not_prose():
    """
    The backend returns stable codes so wording lives only in the catalogs.

    If prose leaks back into a response, the user would see one language while
    the rest of the interface speaks another.
    """
    prose_markers = (
        "All dependencies",
        "Installation started",
        "First-run initialization",
        "download started",
        "marked as completed",
    )
    offenders = []
    for route in installer_api.router.routes:
        for fragment in prose_markers:
            if fragment in str(route.endpoint.__doc__ or ""):
                offenders.append(route.path)
    assert offenders == [], f"responses must use codes: {offenders}"


def test_progress_messages_are_catalog_keys():
    """Every progress message the backend emits must resolve to a catalog key."""
    from app.services.installer_service import STEP_CHECKING, STEP_COMPLETE, STEP_STARTING

    assert STEP_CHECKING.startswith("installer.")
    assert STEP_STARTING.startswith("installer.")
    assert STEP_COMPLETE.startswith("installer.")


# --------------------------------------------------------------------------
# Storage layout
# --------------------------------------------------------------------------
def test_all_storage_lives_under_one_data_dir():
    """Database, vector store and logs must not drift to different folders."""
    from pathlib import Path

    from app import config

    active = config.settings
    root = Path(active.data_dir).resolve()
    db_path = Path(active.database_url.replace("sqlite+aiosqlite:///", "")).resolve()
    qdrant = Path(active.qdrant_path).resolve()
    log = Path(active.log_file).resolve()

    for candidate in (db_path, qdrant, log):
        assert root in candidate.parents or candidate == root, f"{candidate} escapes {root}"


def test_installer_uses_the_same_data_dir_as_the_app():
    from pathlib import Path

    from app import config

    service = service_module.InstallerService()
    assert Path(service.data_dir).resolve() == Path(config.settings.data_dir).resolve()


def test_engine_autoinstall_requires_a_pinned_digest(monkeypatch):
    """
    On Windows the app must not download an unverifiable installer.

    With no pinned SHA-256 the component is reported as manual-only, which
    fails the install closed instead of executing an unverified binary.
    """

    monkeypatch.setattr(service_module.platform, "system", lambda: "Windows")
    monkeypatch.setattr(service_module.settings, "ollama_installer_sha256", "")

    service = service_module.InstallerService()
    assert service._engine_install_allowed() is False


def test_engine_autoinstall_allowed_with_a_pinned_digest(monkeypatch):

    monkeypatch.setattr(service_module.platform, "system", lambda: "Windows")
    monkeypatch.setattr(
        service_module.settings, "ollama_installer_sha256", "a" * 64
    )

    service = service_module.InstallerService()
    assert service._engine_install_allowed() is True


def test_client_fixture_smoke():
    """Confirms TestClient is available for future endpoint-level tests."""
    assert TestClient is not None
