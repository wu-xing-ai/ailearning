"""Authentication utilities: JWT, password hashing, FastAPI dependencies."""

import os
from datetime import datetime, timedelta
from typing import List, Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.database import get_db

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "ailearning-secret-key-change-in-production-2024")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Hash password with bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against bcrypt hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(data: dict) -> str:
    """Create JWT token with expiration."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate JWT token."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的认证令牌")


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    """FastAPI dependency: extract and validate JWT, return user dict.

    Returns None if no token provided (optional auth).
    """
    if credentials is None:
        return None
    from models.user import User

    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="无效的认证令牌")

    db = next(get_db())
    try:
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user:
            raise HTTPException(status_code=401, detail="用户不存在或已禁用")
        return user
    finally:
        db.close()


async def require_auth(
    user=Depends(get_current_user),
):
    """Require authenticated user."""
    if user is None:
        raise HTTPException(status_code=401, detail="请先登录")
    return user


def require_role(allowed_roles: List[str]):
    """Factory for role-checking dependency."""
    async def _check(user=Depends(require_auth)):
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"权限不足，需要角色: {', '.join(allowed_roles)}"
            )
        return user
    return _check
