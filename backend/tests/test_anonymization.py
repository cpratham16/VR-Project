import pytest
from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeMeta

from app.models.anonymized import RegionalAggregate
from app.services.anonymizer import resolve_region, _period_key
from app.models.user import User
from datetime import datetime

def test_regional_aggregate_no_identifier_columns():
    """Schema-review test: RegionalAggregate must contain NO columns capable
    of identifying an individual (no user_id, email, pseudonym, foreign keys)."""
    forbidden = {"user_id", "email", "pseudonym", "patient_id", "doctor_id", "session_id",
                 "name", "contact", "phone", "password_hash"}
    mapper = inspect(RegionalAggregate)
    cols = {c.key for c in mapper.columns}
    # Check columns for foreign keys
    fk_columns = {c.key for c in mapper.columns if c.foreign_keys}
    violations = cols.intersection(forbidden)
    assert not violations, f"RegionalAggregate has identifier columns: {violations}"
    assert not fk_columns, f"RegionalAggregate has foreign key columns: {fk_columns}"
    assert "region" in cols, "RegionalAggregate must have a 'region' column"
    assert "period" in cols, "RegionalAggregate must have a 'period' column"

def test_resolve_region_city_state():
    user = User()
    user.city = "Pune"
    user.state = "Maharashtra"
    assert resolve_region(user) == "Pune, Maharashtra"

def test_resolve_region_state_only():
    user = User()
    user.state = "Maharashtra"
    user.city = None
    assert resolve_region(user) == "Maharashtra"

def test_resolve_region_none():
    user = User()
    user.city = None
    user.state = None
    assert resolve_region(user) == "Unknown Region"

def test_period_key_format():
    ts = datetime(2026, 8, 15, 12, 30, 0)
    assert _period_key(ts) == "2026-08"

def test_period_key_fallback():
    assert _period_key(None) == datetime.utcnow().strftime("%Y-%m")
