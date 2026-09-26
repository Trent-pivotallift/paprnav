from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import SESSION_COOKIE_NAME, get_current_user
from app.api.routes.admin import ensure_platform_admin
from app.core.config import get_settings
from app.core.security import create_session_token, hash_password, hash_session_token, verify_password
from app.db.session import get_db
from app.models.core import AuthSession, Organization, OrganizationMembership, User
from app.schemas.auth import (
    AuthResponse,
    CurrentUserResponse,
    InvitationAcceptRequest,
    InvitationCreateRequest,
    InvitationCreateResponse,
    LoginRequest,
    MembershipResponse,
    OkResponse,
    ProfileUpdateRequest,
    RegisterRequest,
)
from app.services.invitations import InvitationError, create_invitation, verify_invitation
from app.services.observability import record_product_event
from app.services.pilot_achievements import record_pilot_achievement

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

SESSION_TTL_DAYS = 7


def normalize_email(email: str) -> str:
    return email.strip().lower()


def serialize_user(user: User) -> CurrentUserResponse:
    memberships = [
        MembershipResponse(
            organizationId=membership.organization.id,
            organizationName=membership.organization.name,
            role=membership.role,
        )
        for membership in user.memberships
        if membership.status == "active"
    ]
    return CurrentUserResponse(id=user.id, email=user.email, name=user.name, memberships=memberships)


def create_session(db: Session, user: User, request: Request, response: Response) -> None:
    token = create_session_token()
    auth_session = AuthSession(
        user_id=user.id,
        token_hash=hash_session_token(token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=SESSION_TTL_DAYS),
        user_agent=request.headers.get("user-agent"),
    )
    db.add(auth_session)
    db.flush()

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=get_settings().session_cookie_secure,
        max_age=SESSION_TTL_DAYS * 24 * 60 * 60,
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, request: Request, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    if get_settings().environment == "pilot":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    email = normalize_email(payload.email)
    existing_user = db.scalar(select(User).where(User.email == email))
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")

    user = User(email=email, name=payload.name.strip(), password_hash=hash_password(payload.password), status="active")
    db.add(user)
    db.flush()
    create_session(db, user, request, response)
    record_product_event(db, event_type="auth_register", subject_type="auth", subject_id=user.id, actor=user)
    db.commit()
    db.refresh(user)
    return AuthResponse(user=serialize_user(user))


@router.post("/invitations", response_model=InvitationCreateResponse)
def generate_invitation(
    payload: InvitationCreateRequest,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InvitationCreateResponse:
    ensure_platform_admin(current_user)
    settings = get_settings()
    if not settings.invite_signing_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Invitation service is unavailable",
        )
    try:
        code, expires_at = create_invitation(
            secret=settings.invite_signing_secret,
            email=payload.email,
            name=payload.name,
            organization_name=payload.organizationName,
            organization_type=payload.organizationType,
            role=payload.role,
            ttl=timedelta(hours=payload.expiresInHours),
        )
    except InvitationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid invitation request",
        ) from exc
    record_product_event(
        db,
        event_type="invite_generated",
        subject_type="invitation",
        actor=current_user,
        properties={
            "organizationType": payload.organizationType,
            "role": payload.role,
            "expiresAt": expires_at.isoformat(),
        },
    )
    db.commit()
    response.headers["Cache-Control"] = "no-store"
    return InvitationCreateResponse(invitationCode=code, expiresAt=expires_at)


@router.post(
    "/invitations/accept",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
def accept_invitation(
    payload: InvitationAcceptRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthResponse:
    settings = get_settings()
    if not settings.invite_signing_secret:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation could not be accepted",
        )
    try:
        claims = verify_invitation(
            payload.invitationCode,
            secret=settings.invite_signing_secret,
        )
        if db.scalar(select(User.id).where(User.email == claims.email)) is not None:
            raise InvitationError("invitation already used")
        user = User(
            email=claims.email,
            name=claims.name,
            password_hash=hash_password(payload.password),
            status="active",
        )
        organization = Organization(
            name=claims.organization_name,
            type=claims.organization_type,
        )
        db.add_all([user, organization])
        db.flush()
        db.add(
            OrganizationMembership(
                organization_id=organization.id,
                user_id=user.id,
                role=claims.role,
                status="active",
            )
        )
        db.flush()
        create_session(db, user, request, response)
        record_pilot_achievement(
            db,
            event_type="invite_accepted",
            subject_type="user",
            subject_id=user.id,
            actor=user,
            organization_id=organization.id,
        )
        db.commit()
        db.refresh(user)
    except (InvitationError, IntegrityError, ValueError):
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation could not be accepted",
        ) from None
    response.headers["Cache-Control"] = "no-store"
    return AuthResponse(user=serialize_user(user))


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    email = normalize_email(payload.email)
    user = db.scalar(select(User).where(User.email == email))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if user.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not active")

    create_session(db, user, request, response)
    record_product_event(db, event_type="auth_login", subject_type="auth", subject_id=user.id, actor=user)
    db.commit()
    db.refresh(user)
    return AuthResponse(user=serialize_user(user))


@router.get("/me", response_model=AuthResponse)
def me(current_user: User = Depends(get_current_user)) -> AuthResponse:
    return AuthResponse(user=serialize_user(current_user))


@router.patch("/profile", response_model=AuthResponse)
def update_profile(
    payload: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AuthResponse:
    current_user.name = payload.name.strip()
    record_product_event(
        db,
        event_type="profile_updated",
        subject_type="profile",
        subject_id=current_user.id,
        actor=current_user,
    )
    db.commit()
    db.refresh(current_user)
    return AuthResponse(user=serialize_user(current_user))


@router.post("/logout", response_model=OkResponse)
def logout(
    response: Response,
    session_token: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    db: Session = Depends(get_db),
) -> OkResponse:
    if session_token:
        auth_session = db.scalar(select(AuthSession).where(AuthSession.token_hash == hash_session_token(session_token)))
        if auth_session and auth_session.revoked_at is None:
            auth_session.revoked_at = datetime.now(timezone.utc)
            db.commit()

    response.delete_cookie(
        SESSION_COOKIE_NAME,
        secure=get_settings().session_cookie_secure,
        httponly=True,
        samesite="lax",
    )
    return OkResponse(ok=True)
