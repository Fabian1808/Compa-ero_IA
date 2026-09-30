from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    name: str
    avatar_url: str | None = None


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    name: str | None = None
    avatar_url: str | None = None
    preferences_json: str | None = None


class UserResponse(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SessionResponse(BaseModel):
    """The caller's session, including the role they hold in the active tenant.

    Roles are per tenant, so they are resolved server-side and shipped as a
    ready-made ``is_admin`` flag. The client must not re-derive admin status from
    the role string, or it can drift from what the API actually enforces.
    """

    user: UserResponse
    tenant_id: str | None = None
    tenant_name: str | None = None
    role: str | None = None
    is_admin: bool = False
