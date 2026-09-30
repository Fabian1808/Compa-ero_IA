"""
Authorization tests for tenant-scoped roles.

Roles live on the `TenantUser` membership, not on the user record, so the admin
gate is the single place that decides whether a caller may administer a tenant.
These tests exercise that decision directly with a stubbed session, which keeps
them focused on the authorization rule rather than on database setup.
"""

from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.multi_tenancy.middleware import require_tenant_admin
from app.multi_tenancy.models import (
    TENANT_ADMIN_ROLES,
    TENANT_ROLES,
    TenantUser,
)


def make_request(user=None, tenant=None):
    """Build a request whose state looks like TenantMiddleware left it."""
    scope = {"type": "http", "method": "GET", "path": "/admin/tenants", "headers": []}
    request = Request(scope)
    if tenant is not None:
        request.state.tenant = tenant
        request.state.tenant_id = tenant.id
    if user is not None:
        request.state.current_user = user
        request.state.user_id = user.id
    return request


class StubSession:
    """Returns a preset membership row, or None when there is no membership."""

    def __init__(self, membership):
        self._membership = membership
        self.queried = False

    async def scalar(self, statement):
        self.queried = True
        return self._membership


def membership(role):
    return SimpleNamespace(
        id="membership-1",
        tenant_id="tenant-1",
        user_id="user-1",
        role=role,
        is_active=True,
    )


USER = SimpleNamespace(id="user-1", email="ana@example.com", name="Ana")
TENANT = SimpleNamespace(id="tenant-1", name="Acme")


@pytest.mark.parametrize("role", sorted(TENANT_ADMIN_ROLES))
def test_owner_and_admin_are_allowed(role):
    db = StubSession(membership(role))

    result = _run(require_tenant_admin, make_request(USER, TENANT), db)

    assert result is USER
    assert db.queried is True


@pytest.mark.parametrize("role", ["member", "viewer"])
def test_member_and_viewer_are_rejected(role):
    db = StubSession(membership(role))

    with pytest.raises(HTTPException) as excinfo:
        _run(require_tenant_admin, make_request(USER, TENANT), db)

    assert excinfo.value.status_code == 403
    assert db.queried is True


def test_non_member_is_rejected():
    db = StubSession(None)

    with pytest.raises(HTTPException) as excinfo:
        _run(require_tenant_admin, make_request(USER, TENANT), db)

    assert excinfo.value.status_code == 403


def test_unknown_role_is_rejected():
    """A role string that is not one of the known values must not grant access."""
    db = StubSession(membership("superuser"))

    with pytest.raises(HTTPException) as excinfo:
        _run(require_tenant_admin, make_request(USER, TENANT), db)

    assert excinfo.value.status_code == 403


def test_anonymous_caller_is_rejected_without_querying_the_database():
    db = StubSession(membership("admin"))

    with pytest.raises(HTTPException) as excinfo:
        _run(require_tenant_admin, make_request(None, TENANT), db)

    assert excinfo.value.status_code == 401
    assert db.queried is False


def test_role_constants_cover_every_stored_role():
    assert {"owner", "admin", "member", "viewer"} == TENANT_ROLES
    assert {"owner", "admin"} == TENANT_ADMIN_ROLES
    assert TENANT_ADMIN_ROLES < TENANT_ROLES


def test_membership_defaults_to_the_least_privileged_role():
    """The column default must not be an administrative role."""
    column = TenantUser.__table__.c.role
    assert column.default.arg == "member"
    assert column.default.arg not in TENANT_ADMIN_ROLES


def _run(coro, request, db):
    """Drive an async dependency without pulling in an event loop per test."""
    import asyncio

    return asyncio.run(coro(request, db))
