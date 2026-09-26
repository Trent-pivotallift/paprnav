from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models.core import AuthSession
from app.services.observability import record_product_event


def revoke_auth_sessions(db: Session, *, user_id: str | None) -> int:
    statement = update(AuthSession).where(AuthSession.revoked_at.is_(None))
    if user_id is not None:
        statement = statement.where(AuthSession.user_id == user_id)
    result = db.execute(statement.values(revoked_at=datetime.now(timezone.utc)))
    revoked_count = result.rowcount or 0
    record_product_event(
        db,
        event_type="operator_sessions_revoked",
        subject_type="user" if user_id else "session_population",
        subject_id=user_id or "all",
        event_source="operator_cli",
        properties={"revokedCount": revoked_count},
    )
    return revoked_count
