from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    email: str
    name: str = Field(min_length=1)
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: str
    password: str


class InvitationCreateRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    name: str = Field(min_length=1, max_length=255)
    organizationName: str = Field(min_length=1, max_length=255)
    organizationType: Literal["owner", "maintenance_shop"]
    role: Literal["owner_admin", "maintenance_admin"]
    expiresInHours: int = Field(default=24, ge=1, le=24)


class InvitationCreateResponse(BaseModel):
    invitationCode: str
    expiresAt: datetime


class InvitationAcceptRequest(BaseModel):
    invitationCode: str = Field(min_length=1, max_length=4096)
    password: str = Field(min_length=8, max_length=1024)


class MembershipResponse(BaseModel):
    organizationId: str
    organizationName: str
    role: str


class CurrentUserResponse(BaseModel):
    id: str
    email: str
    name: str
    memberships: list[MembershipResponse] = []


class ProfileUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class AuthResponse(BaseModel):
    user: CurrentUserResponse


class OkResponse(BaseModel):
    ok: bool
