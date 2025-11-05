from __future__ import annotations
import os, sqlite3, datetime, jwt, bcrypt
from pathlib import Path
from typing import Optional, Tuple
from app.data.db_config import get_connection

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")
JWT_ALG = "HS256"
ACCESS_MIN = int(os.getenv("JWT_ACCESS_MIN", "60"))
REFRESH_MIN = int(os.getenv("JWT_REFRESH_MIN", "1440"))

def verify_user(username: str, password: str) -> Optional[dict]:
    with get_connection() as con:
        row = con.execute("SELECT id, username, password_hash, role, is_active FROM users WHERE username=?",
                          (username,)).fetchone()
    if not row or not row["is_active"]:
        return None
    if not bcrypt.checkpw(password.encode(), row["password_hash"].encode()):
        return None
    return dict(row)

def _jwt(now: datetime.datetime, sub: str, role: str, minutes: int, typ: str) -> str:
    payload = {
        "sub": sub, "role": role, "typ": typ,
        "iat": int(now.timestamp()),
        "exp": int((now + datetime.timedelta(minutes=minutes)).timestamp()),
        "iss": "aisa.local"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def issue_tokens(username: str, role: str) -> Tuple[str, str]:
    now = datetime.datetime.utcnow()
    return _jwt(now, username, role, ACCESS_MIN, "access"), _jwt(now, username, role, REFRESH_MIN, "refresh")

def verify_access(token: str) -> dict:
    claims = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    if claims.get("typ") != "access":
        raise ValueError("wrong token type")
    return claims

def verify_refresh(token: str) -> dict:
    claims = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    if claims.get("typ") != "refresh":
        raise ValueError("wrong token type")
    return claims
