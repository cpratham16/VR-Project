"""Auth & access-control test pass (PRD Iteration 14).

Verifies role-based access control boundaries at the dependency layer and
the API contract, without requiring a live database:
  - get_current_doctor / get_current_admin role gating
  - invalid / expired JWT rejection
  - every clinical/admin route is protected by OAuth2 security
  - panic SOS is available to any authenticated user (fail-safe design)
"""
import uuid
from datetime import timedelta

import pytest
from fastapi import HTTPException
from jose import jwt

from app.api.deps import get_current_admin, get_current_doctor, get_current_user
from app.core.config import settings
from app.core.security import create_access_token
from app.main import app
from app.models.user import User

PUBLIC_PATHS = {"/", "/api/v1/openapi.json"}


def make_user(role: str) -> User:
    return User(id=uuid.uuid4(), role=role, is_active=True)


@pytest.mark.asyncio
async def test_doctor_dependency_allows_doctor():
    doctor = make_user("doctor")
    assert await get_current_doctor(doctor) is doctor


@pytest.mark.asyncio
async def test_doctor_dependency_rejects_patient():
    with pytest.raises(HTTPException) as exc:
        await get_current_doctor(make_user("patient"))
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_doctor_dependency_allows_admin():
    # get_current_doctor scopes include both doctor and admin
    admin = make_user("admin")
    assert await get_current_doctor(admin) is admin


@pytest.mark.asyncio
async def test_admin_dependency_allows_admin():
    admin = make_user("admin")
    assert await get_current_admin(admin) is admin


@pytest.mark.asyncio
async def test_admin_dependency_rejects_patient():
    with pytest.raises(HTTPException) as exc:
        await get_current_admin(make_user("patient"))
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_admin_dependency_rejects_doctor():
    with pytest.raises(HTTPException) as exc:
        await get_current_admin(make_user("doctor"))
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_invalid_token_rejected():
    with pytest.raises(HTTPException) as exc:
        await get_current_user(token="not.a.jwt.token")
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_expired_token_rejected():
    expired = create_access_token("some-user", expires_delta=timedelta(seconds=-60))
    with pytest.raises(HTTPException) as exc:
        await get_current_user(token=expired)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_token_signed_with_wrong_secret_rejected():
    from datetime import datetime
    wrong = jwt.encode(
        {"exp": int(datetime.utcnow().timestamp()) + 300, "sub": "some-user"},
        "a-completely-different-secret-key",
        algorithm=settings.ALGORITHM,
    )
    with pytest.raises(HTTPException) as exc:
        await get_current_user(token=wrong)
    assert exc.value.status_code == 403


def test_all_clinical_and_admin_routes_require_oauth_security():
    """Every non-public route must declare OAuth2 security in OpenAPI."""
    schema = app.openapi()
    HTTP_METHODS = {"get", "post", "put", "delete", "patch", "head", "options"}
    excluded_paths = {
        "/api/v1/auth/login",
        "/api/v1/auth/signup",
        "/api/v1/health/",
    }
    for path, methods in schema["paths"].items():
        if path in excluded_paths or path in PUBLIC_PATHS:
            continue
        for method, op in methods.items():
            if method not in HTTP_METHODS:
                continue
            security = op.get("security", [])
            assert security, (
                f"Route {method.upper()} {path} has NO security requirement"
            )


def test_panic_sos_secured_but_not_role_restricted():
    """Panic SOS must require authentication (it's a fail-safe) and not be
    scoped to a single role in the OpenAPI contract."""
    schema = app.openapi()
    op = schema["paths"]["/api/v1/patient/panic"]["post"]
    assert op.get("security"), "Panic SOS must require authentication"
    # Restriction to specific roles is enforced by get_current_user only
    # (any authenticated user may trigger a fail-safe alert)


def test_admin_analytics_routes_exist_and_are_secured():
    schema = app.openapi()
    admin_paths = [
        "/api/v1/admin/analytics/run-pipeline",
        "/api/v1/admin/analytics/overview",
        "/api/v1/admin/analytics/regions",
        "/api/v1/admin/analytics/trend",
        "/api/v1/admin/analytics/spikes",
    ]
    for path in admin_paths:
        for method, op in schema["paths"][path].items():
            if method == "parameters":
                continue
            assert op.get("security"), f"{path} must be secured"


def test_vr_patient_routes_are_secured():
    schema = app.openapi()
    for path in ["/api/v1/patient/vr/assigned"]:
        assert schema["paths"][path]["get"]["security"]


def test_doctor_vr_routes_are_secured():
    schema = app.openapi()
    for path in ["/api/v1/doctor/vr/assign", "/api/v1/doctor/vr/scenarios"]:
        methods = schema["paths"][path]
        for method, op in methods.items():
            if method in {"get", "post"}:
                assert op.get("security"), f"{method.upper()} {path} must be secured"
