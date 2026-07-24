import json
import os
import sys
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt, JWTError

_secret = os.getenv("JWT_SECRET")
if not _secret:
    raise RuntimeError("JWT_SECRET environment variable is required")
SECRET_KEY = _secret
ALGORITHM = "HS256"
EXPIRE_HOURS = 8
USERS_FILE = os.getenv("USERS_FILE", os.path.join(os.path.dirname(__file__), "users.json"))

_DUMMY_HASH = bcrypt.hashpw(b"dummy", bcrypt.gensalt()).decode()


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_token(email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=EXPIRE_HOURS)
    return jwt.encode({"sub": email, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> str:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    sub = payload.get("sub")
    if not sub:
        raise JWTError("Missing sub claim")
    return sub


def authenticate_user(email: str, password: str) -> bool:
    try:
        with open(USERS_FILE) as f:
            users = json.load(f)
    except FileNotFoundError:
        return False
    user = next((u for u in users if u["email"] == email), None)
    # Always run verify to prevent email enumeration via timing
    candidate_hash = user["password_hash"] if user else _DUMMY_HASH
    return verify_password(password, candidate_hash) and user is not None


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "create-user":
        import getpass
        email = sys.argv[2]
        users = []
        try:
            with open(USERS_FILE) as f:
                users = json.load(f)
        except FileNotFoundError:
            pass
        if any(u["email"] == email for u in users):
            print(f"Usuario {email} ja existe.")
            sys.exit(1)
        password = getpass.getpass("Password: ")
        users.append({"email": email, "password_hash": hash_password(password)})
        with open(USERS_FILE, "w") as f:
            json.dump(users, f, indent=2)
        print(f"Usuario {email} criado.")
