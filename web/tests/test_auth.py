import json
import os
import pytest
import sys
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-pytest-32chars!!")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from auth import hash_password, verify_password, create_token, verify_token, authenticate_user

def test_password_hash_and_verify():
    hashed = hash_password("secret123")
    assert verify_password("secret123", hashed)
    assert not verify_password("wrong", hashed)

def test_create_and_verify_token():
    token = create_token("test@praxis.com")
    assert verify_token(token) == "test@praxis.com"

def test_invalid_token_raises():
    with pytest.raises(Exception):
        verify_token("not-a-valid-token")

def test_authenticate_user(tmp_path, monkeypatch):
    users = [{"email": "admin@praxis.com", "password_hash": hash_password("pass123")}]
    users_file = tmp_path / "users.json"
    users_file.write_text(json.dumps(users))
    import auth
    monkeypatch.setattr(auth, "USERS_FILE", str(users_file))
    assert authenticate_user("admin@praxis.com", "pass123")
    assert not authenticate_user("admin@praxis.com", "wrong")
    assert not authenticate_user("other@praxis.com", "pass123")

def test_authenticate_user_missing_file(tmp_path, monkeypatch):
    import auth
    monkeypatch.setattr(auth, "USERS_FILE", str(tmp_path / "nonexistent.json"))
    assert not authenticate_user("any@praxis.com", "anypass")
