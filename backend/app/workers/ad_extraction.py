from app.db.session import SessionLocal
from app.services.ad_extraction import process_pending_ad_extractions


def main() -> None:
    with SessionLocal() as db:
        stats = process_pending_ad_extractions(db)
    print(f"ad_extraction seen={stats['seen']} extracted={stats['extracted']} review_queued={stats['review_queued']}")


if __name__ == "__main__":
    main()
