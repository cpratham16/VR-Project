import pytest
from app.core.security import get_password_hash, verify_password, create_access_token
from jose import jwt
from app.core.config import settings

def test_password_hashing():
    raw_pass = "SecurePass123"
    hashed = get_password_hash(raw_pass)
    assert hashed != raw_pass
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPass", hashed) is False

def test_jwt_token_creation():
    subject = "user-uuid-1234"
    token = create_access_token(subject)
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["sub"] == subject
    assert "exp" in payload
