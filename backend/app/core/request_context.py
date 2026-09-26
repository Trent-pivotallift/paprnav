from __future__ import annotations

from contextvars import ContextVar, Token
import re
from uuid import uuid4


CORRELATION_ID_HEADER = "X-Correlation-ID"
_CORRELATION_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_correlation_id: ContextVar[str | None] = ContextVar(
    "paprnav_correlation_id",
    default=None,
)


def valid_correlation_id(value: str | None) -> bool:
    return bool(value and _CORRELATION_ID_PATTERN.fullmatch(value))


def choose_correlation_id(value: str | None) -> str:
    return value if valid_correlation_id(value) else uuid4().hex


def set_correlation_id(value: str | None) -> Token[str | None]:
    return _correlation_id.set(value)


def reset_correlation_id(token: Token[str | None]) -> None:
    _correlation_id.reset(token)


def get_correlation_id() -> str | None:
    return _correlation_id.get()
