from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    email: str
    name: str = Field(min_length=1)
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: str
    password: str


class MembershipResponse(BaseModel):
    organizationId: str
    organizationName: str
    role: str


class CurrentUserResponse(BaseModel):
    id: str
    email: str
    name: str
    memberships: list[MembershipResponse] = []


class AuthResponse(BaseModel):
    user: CurrentUserResponse


class OkResponse(BaseModel):
    ok: bool
