import argparse

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.core import Aircraft
from app.services.ad_matching import match_aircraft_ads


def main() -> None:
    parser = argparse.ArgumentParser(description="Run first-pass AD to logbook matching.")
    parser.add_argument("--aircraft-id", help="Run matching for one aircraft id.")
    args = parser.parse_args()

    with SessionLocal() as db:
        aircraft_ids = [args.aircraft_id] if args.aircraft_id else list(db.scalars(select(Aircraft.id)).all())
        for aircraft_id in aircraft_ids:
            stats = match_aircraft_ads(db, aircraft_id)
            print(
                "ad_matching "
                f"aircraft_id={aircraft_id} "
                f"directives_seen={stats['directives_seen']} "
                f"matched={stats['matched']} "
                f"unresolved={stats['unresolved']} "
                f"review_tasks={stats['review_tasks']} "
                f"skipped_not_applicable={stats['skipped_not_applicable']}"
            )


if __name__ == "__main__":
    main()
