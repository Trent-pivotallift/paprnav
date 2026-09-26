from __future__ import annotations

import argparse

from app.db.session import SessionLocal
from app.services.session_revocation import revoke_auth_sessions


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Revoke active paprnav sessions and write an operator audit event.",
    )
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--user-id")
    target.add_argument("--all", action="store_true")
    args = parser.parse_args()
    with SessionLocal() as db:
        count = revoke_auth_sessions(
            db,
            user_id=None if args.all else args.user_id,
        )
        db.commit()
    print(f"revoked_sessions={count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
