import argparse

from app.db.session import SessionLocal
from app.services.ad_discovery import discover_federal_register_ads


def main() -> None:
    parser = argparse.ArgumentParser(description="Discover FAA AD candidates from the Federal Register API.")
    parser.add_argument("--term", default="Airworthiness Directives", help="Federal Register search term.")
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--per-page", type=int, default=20)
    args = parser.parse_args()

    with SessionLocal() as db:
        stats = discover_federal_register_ads(db, page=args.page, per_page=args.per_page, term=args.term)
    print(
        "ad_discovery "
        f"term={args.term!r} "
        f"seen={stats['seen']} "
        f"candidates={stats['candidates']} "
        f"rejected={stats['rejected']}"
    )


if __name__ == "__main__":
    main()
