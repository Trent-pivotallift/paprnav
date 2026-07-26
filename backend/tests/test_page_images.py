from dataclasses import replace

from app.core.config import get_settings
from app.models.core import IngestionPage, Upload
from app.services import page_images
from app.services.storage import StoredFile


def test_pdf_page_image_uses_source_upload_storage_backend(monkeypatch, tmp_path) -> None:
    settings = replace(
        get_settings(),
        local_storage_path=str(tmp_path),
        storage_backend="local",
        s3_upload_bucket="test-bucket",
    )
    upload = Upload(
        id="upl_page_image",
        aircraft_id="ac_page_image",
        uploaded_by_user_id="usr_page_image",
        original_filename="logbook.pdf",
        content_type="application/pdf",
        file_size_bytes=10,
        storage_backend="s3",
        storage_key="uploads/ac_page_image/upl_page_image/logbook.pdf",
        sha256="0" * 64,
        status="stored",
        pilot_consent_accepted=True,
        cost_allocation_tags={"BillableAccount": "acct-test"},
    )
    page = IngestionPage(
        ingestion_job_id="job_page_image",
        upload_id=upload.id,
        source_page_number=1,
        current_page_order=1,
    )
    captured = {}

    monkeypatch.setattr(page_images, "read_stored_file_bytes", lambda **_kwargs: b"%PDF")
    monkeypatch.setattr(page_images, "render_pdf_page_png", lambda *_args, **_kwargs: b"\x89PNG\r\n\x1a\n" + b"\0" * 16)
    monkeypatch.setattr(page_images, "pdftoppm_version", lambda: "pdftoppm version test")
    monkeypatch.setattr(
        page_images,
        "rendered_visual_metrics",
        lambda _data: {"aspectRatio": 1.0, "meanLuminance": 240.0, "luminanceStdDev": 30.0},
    )

    def fake_store_bytes(data, *, settings, storage_key, content_type, cost_allocation_tags):
        captured["storage_backend"] = settings.storage_backend
        captured["storage_key"] = storage_key
        return StoredFile(storage_key, len(data), "1" * 64, storage_backend=settings.storage_backend)

    monkeypatch.setattr(page_images, "store_bytes", fake_store_bytes)

    page_images.attach_page_image(settings=settings, upload=upload, page=page)

    assert captured["storage_backend"] == "s3"
    assert page.image_storage_backend == "s3"
    assert page.image_storage_key == captured["storage_key"]
    assert page.render_profile == "canonical-pdf-page-v1"
    assert len(page.canonical_image_sha256) == 64
    assert page.render_metadata["dpi"] == 300
    assert page.render_metadata["colorMode"] == "rgb"
    assert page.render_metadata["deskewApplied"] is False
