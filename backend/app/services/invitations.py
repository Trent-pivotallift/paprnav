from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any


INVITATION_VERSION = 1
MAX_INVITATION_TTL = timedelta(hours=24)
INVITATION_CLOCK_SKEW = timedelta(minutes=5)
ALLOWED_ROLE_TYPES = {
    ("owner", "owner_admin"),
    ("maintenance_shop", "maintenance_admin"),
}
INVITATION_KEYS = {
    "email",
    "exp",
    "iat",
    "name",
    "nonce",
    "organizationName",
    "organizationType",
    "role",
    "version",
}


class InvitationError(ValueError):
    pass


@dataclass(frozen=True)
class InvitationClaims:
    email: str
    name: str
    organization_name: str
    organization_type: str
    role: str
    nonce: str
    issued_at: datetime
    expires_at: datetime


def normalize_email(email: str) -> str:
    return email.strip().lower()


def _encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _decode(value: str) -> bytes:
    if not value or any(character.isspace() for character in value):
        raise InvitationError("invalid invitation")
    try:
        return base64.b64decode(
            value.encode("ascii") + b"=" * (-len(value) % 4),
            altchars=b"-_",
            validate=True,
        )
    except (UnicodeEncodeError, ValueError) as exc:
        raise InvitationError("invalid invitation") from exc


def _canonical_payload(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def create_invitation(
    *,
    secret: str,
    email: str,
    name: str,
    organization_name: str,
    organization_type: str,
    role: str,
    now: datetime | None = None,
    ttl: timedelta = MAX_INVITATION_TTL,
) -> tuple[str, datetime]:
    normalized_email = normalize_email(email)
    clean_name = name.strip()
    clean_organization_name = organization_name.strip()
    if not normalized_email or not clean_name or not clean_organization_name:
        raise InvitationError("invalid invitation fields")
    if (organization_type, role) not in ALLOWED_ROLE_TYPES:
        raise InvitationError("invalid invitation role")
    if ttl <= timedelta(0) or ttl > MAX_INVITATION_TTL:
        raise InvitationError("invalid invitation lifetime")
    issued_at = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).replace(microsecond=0)
    expires_at = issued_at + ttl
    payload = {
        "email": normalized_email,
        "exp": int(expires_at.timestamp()),
        "iat": int(issued_at.timestamp()),
        "name": clean_name,
        "nonce": secrets.token_urlsafe(24),
        "organizationName": clean_organization_name,
        "organizationType": organization_type,
        "role": role,
        "version": INVITATION_VERSION,
    }
    payload_bytes = _canonical_payload(payload)
    signature = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).digest()
    return f"{_encode(payload_bytes)}.{_encode(signature)}", expires_at


def verify_invitation(
    token: str,
    *,
    secret: str,
    now: datetime | None = None,
) -> InvitationClaims:
    try:
        payload_part, signature_part = token.split(".")
    except ValueError as exc:
        raise InvitationError("invalid invitation") from exc
    payload_bytes = _decode(payload_part)
    signature = _decode(signature_part)
    expected = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).digest()
    if not hmac.compare_digest(signature, expected):
        raise InvitationError("invalid invitation")
    try:
        payload = json.loads(payload_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvitationError("invalid invitation") from exc
    if not isinstance(payload, dict) or set(payload) != INVITATION_KEYS:
        raise InvitationError("invalid invitation")
    if _canonical_payload(payload) != payload_bytes:
        raise InvitationError("invalid invitation")
    if type(payload.get("version")) is not int or payload["version"] != INVITATION_VERSION:
        raise InvitationError("invalid invitation")
    string_keys = INVITATION_KEYS - {"version", "iat", "exp"}
    if any(not isinstance(payload.get(key), str) or not payload[key] for key in string_keys):
        raise InvitationError("invalid invitation")
    if type(payload.get("iat")) is not int or type(payload.get("exp")) is not int:
        raise InvitationError("invalid invitation")
    if normalize_email(payload["email"]) != payload["email"]:
        raise InvitationError("invalid invitation")
    try:
        nonce = _decode(payload["nonce"])
    except InvitationError as exc:
        raise InvitationError("invalid invitation") from exc
    if len(nonce) != 24 or _encode(nonce) != payload["nonce"]:
        raise InvitationError("invalid invitation")
    if payload["name"].strip() != payload["name"] or payload["organizationName"].strip() != payload["organizationName"]:
        raise InvitationError("invalid invitation")
    if (payload["organizationType"], payload["role"]) not in ALLOWED_ROLE_TYPES:
        raise InvitationError("invalid invitation")
    try:
        issued_at = datetime.fromtimestamp(payload["iat"], timezone.utc)
        expires_at = datetime.fromtimestamp(payload["exp"], timezone.utc)
    except (OverflowError, OSError, ValueError) as exc:
        raise InvitationError("invalid invitation") from exc
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if issued_at > current + INVITATION_CLOCK_SKEW:
        raise InvitationError("invalid invitation")
    if expires_at <= current - INVITATION_CLOCK_SKEW:
        raise InvitationError("invalid invitation")
    if expires_at <= issued_at or expires_at - issued_at > MAX_INVITATION_TTL:
        raise InvitationError("invalid invitation")
    return InvitationClaims(
        email=payload["email"],
        name=payload["name"],
        organization_name=payload["organizationName"],
        organization_type=payload["organizationType"],
        role=payload["role"],
        nonce=payload["nonce"],
        issued_at=issued_at,
        expires_at=expires_at,
    )
