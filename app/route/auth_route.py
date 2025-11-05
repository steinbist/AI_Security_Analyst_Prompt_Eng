from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from app.services.auth_service import verify_user, issue_tokens, verify_access, verify_refresh

router = APIRouter(prefix="/auth", tags=["auth"])

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

@router.post("/login", response_model=TokenPair)
def login(body: LoginRequest):
    user = verify_user(body.username, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="invalid credentials")
    access, refresh = issue_tokens(user["username"], user["role"])
    return TokenPair(access_token=access, refresh_token=refresh)

class RefreshRequest(BaseModel):
    refresh_token: str

@router.post("/refresh", response_model=TokenPair)
def refresh(body: RefreshRequest):
    claims = verify_refresh(body.refresh_token)  # raises on error
    access, refresh = issue_tokens(claims["sub"], claims["role"])
    return TokenPair(access_token=access, refresh_token=refresh)

# Dependency to protect routes
def require_jwt(authorization: str = Header(None)) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        claims = verify_access(token)
        return claims
    except Exception as ex:
        raise HTTPException(status_code=401, detail=f"invalid token: {type(ex).__name__}")
