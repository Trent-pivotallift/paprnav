from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.db.session import SessionLocal
from app.services.ad_compliance_population import prepare_full_text_compliance_reviews


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepare retained full-text AD compliance reviews for an aircraft"
    )
    parser.add_argument("--n-number", default="N3671L")
    parser.add_argument("--expected-publications", type=int, default=17)
    parser.add_argument("--output")
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Persist queued reviews; default behavior rolls the preparation back",
    )
    args = parser.parse_args()

    with SessionLocal() as db:
        report = prepare_full_text_compliance_reviews(
            db,
            n_number=args.n_number,
            expected_publications=args.expected_publications,
        )
        if args.commit:
            db.commit()
        else:
            db.rollback()

    if args.output:
        destination = Path(args.output)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    verification = report["verification"]
    print(json.dumps(report, sort_keys=True))
    print(f"{verification['passed']} passed out of {verification['total']}")
    if verification["passed"] != verification["total"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
