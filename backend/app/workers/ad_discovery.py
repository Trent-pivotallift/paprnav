from app.db.session import SessionLocal
from app.services.ad_discovery import discover_federal_register_ads


def main() -> None:
    with SessionLocal() as db:
        stats = discover_federal_register_ads(db)
    print(f"ad_discovery seen={stats['seen']} candidates={stats['candidates']} rejected={stats['rejected']}")


if __name__ == "__main__":
    main()
