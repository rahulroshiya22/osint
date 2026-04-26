import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

import database as db

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", "default_secret_change_me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)


def decode_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def generate_api_key():
    return f"tb_{secrets.token_hex(24)}"


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), request: Request = None):
    """Authenticate via JWT token or API key."""
    # Try JWT token first
    if credentials:
        token = credentials.credentials
        # Check if it's an API key
        if token.startswith("tb_"):
            key_data = await db.get_api_key(token)
            if not key_data:
                raise HTTPException(status_code=401, detail="Invalid API key")
            if not key_data["is_active"]:
                raise HTTPException(status_code=403, detail="API key is disabled")
            if key_data["user_status"] != "approved":
                raise HTTPException(status_code=403, detail="Account not approved by admin")
            if key_data["requests_today"] >= key_data["daily_limit"]:
                raise HTTPException(status_code=429, detail="Daily API limit reached")
            await db.increment_api_key_usage(key_data["id"])
            user = await db.get_user_by_id(key_data["user_id"])
            user["auth_type"] = "api_key"
            user["api_key_id"] = key_data["id"]
            return user
        else:
            # It's a JWT token
            payload = decode_token(token)
            if not payload:
                raise HTTPException(status_code=401, detail="Invalid or expired token")
            user = await db.get_user_by_id(payload.get("user_id"))
            if not user:
                raise HTTPException(status_code=401, detail="User not found")
            if user["status"] == "banned":
                raise HTTPException(status_code=403, detail="Account has been banned")
            user["auth_type"] = "jwt"
            user["api_key_id"] = None
            return user

    raise HTTPException(status_code=401, detail="Authentication required")


async def require_approved(user: dict = Depends(get_current_user)):
    """Require the user to be approved."""
    if user["status"] != "approved" and user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Account pending approval. Please wait for admin to approve your account.")
    return user


async def require_admin(user: dict = Depends(get_current_user)):
    """Require the user to be an admin."""
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
