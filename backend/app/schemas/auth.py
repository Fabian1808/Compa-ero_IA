from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None


class AuthInitiateResponse(BaseModel):
    device_code: str
    user_code: str
    verification_uri: str
    expires_in: int
    interval: int
    message: str


class AuthCallbackRequest(BaseModel):
    device_code: str


class AuthStatusResponse(BaseModel):
    authenticated: bool
    user: Optional["UserResponse"] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str