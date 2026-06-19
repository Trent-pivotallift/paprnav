from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.core import IngestionJob
from app.services.ingestion import process_ingestion_job


def main() -> None:
    with SessionLocal() as db:
        jobs = db.scalars(
            select(IngestionJob).where(IngestionJob.ocr_status.in_(["queued", "failed"])).order_by(IngestionJob.created_at)
        ).all()
        for job in jobs:
            process_ingestion_job(db, job)
            print(f"processed {job.id} status={job.status} ocr={job.ocr_status}")
        if not jobs:
            print("no queued OCR jobs")


if __name__ == "__main__":
    main()
