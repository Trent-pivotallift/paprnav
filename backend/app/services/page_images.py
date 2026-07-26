from __future__ import annotations

import shutil
import subprocess
import tempfile
from hashlib import sha256
from dataclasses import replace
from pathlib import Path
from io import BytesIO

from app.core.config import Settings
from app.models.core import IngestionPage, Upload
from app.services.storage import derived_storage_key, read_stored_file_bytes, store_bytes


BUNDLED_PDF_BIN_DIR = Path("/Users/hostiletakeover/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override")
CANONICAL_RENDER_PROFILE = "canonical-pdf-page-v1"
CANONICAL_RENDER_DPI = 300


def find_pdftoppm() -> str | None:
    candidates = [
        shutil.which("pdftoppm"),
        str(BUNDLED_PDF_BIN_DIR / "pdftoppm"),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return candidate
    return None


def pdftoppm_version() -> str | None:
    pdftoppm = find_pdftoppm()
    if pdftoppm is None:
        return None
    try:
        result = subprocess.run(
            [pdftoppm, "-v"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except OSError:
        return None
    version_output = (result.stderr or result.stdout).strip().splitlines()
    return version_output[0][:128] if version_output else None


def render_pdf_page_png(document_bytes: bytes, source_page_number: int, *, dpi: int = 180) -> bytes | None:
    pdftoppm = find_pdftoppm()
    if pdftoppm is None:
        return None

    with tempfile.TemporaryDirectory(prefix="paprnav-page-render-") as temp_dir:
        temp_path = Path(temp_dir)
        input_path = temp_path / "input.pdf"
        output_prefix = temp_path / "page"
        input_path.write_bytes(document_bytes)
        subprocess.run(
            [
                pdftoppm,
                "-f",
                str(source_page_number),
                "-l",
                str(source_page_number),
                "-r",
                str(dpi),
                "-png",
                str(input_path),
                str(output_prefix),
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        rendered = sorted(temp_path.glob("page-*.png"))
        if not rendered:
            return None
        return rendered[0].read_bytes()


def png_dimensions(data: bytes) -> tuple[int, int] | None:
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")


def rendered_visual_metrics(data: bytes) -> dict:
    from PIL import Image, ImageStat

    with Image.open(BytesIO(data)) as source:
        rgb = source.convert("RGB")
        grayscale = rgb.convert("L")
        statistics = ImageStat.Stat(grayscale)
        width, height = rgb.size
        return {
            "aspectRatio": round(width / max(height, 1), 6),
            "meanLuminance": round(statistics.mean[0], 3),
            "luminanceStdDev": round(statistics.stddev[0], 3),
        }


def attach_page_image(
    *,
    settings: Settings,
    upload: Upload,
    page: IngestionPage,
) -> None:
    if upload.content_type in {"image/png", "image/jpeg"}:
        page.image_storage_backend = upload.storage_backend
        page.image_storage_key = upload.storage_key
        return

    if upload.content_type != "application/pdf":
        return

    try:
        document_bytes = read_stored_file_bytes(
            settings=settings,
            storage_backend=upload.storage_backend,
            storage_key=upload.storage_key,
        )
        rendered_page = render_pdf_page_png(
            document_bytes,
            page.source_page_number,
            dpi=CANONICAL_RENDER_DPI,
        )
    except Exception:
        return
    if rendered_page is None:
        return

    image_key = derived_storage_key(
        settings.s3_upload_prefix or "uploads",
        upload.aircraft_id,
        upload.id,
        f"page-images/page-{page.source_page_number:04d}.png",
    )
    artifact_settings = replace(
        settings,
        storage_backend=upload.storage_backend,
    )
    stored = store_bytes(
        rendered_page,
        settings=artifact_settings,
        storage_key=image_key,
        content_type="image/png",
        cost_allocation_tags={
            **(upload.cost_allocation_tags or {}),
            "PaprnavArtifact": "ocr-page-image",
            "SourceUploadId": upload.id,
        },
    )
    page.image_storage_backend = stored.storage_backend
    page.image_storage_key = stored.storage_key
    page.canonical_image_sha256 = sha256(rendered_page).hexdigest()
    page.render_profile = CANONICAL_RENDER_PROFILE
    dimensions = png_dimensions(rendered_page)
    if dimensions:
        page.width_px, page.height_px = dimensions
    page.render_metadata = {
        "profile": CANONICAL_RENDER_PROFILE,
        "renderer": "poppler_pdftoppm",
        "rendererVersion": pdftoppm_version(),
        "dpi": CANONICAL_RENDER_DPI,
        "colorMode": "rgb",
        "format": "png",
        "declaredRotationApplied": True,
        "deskewApplied": False,
        "enhancementApplied": False,
        "widthPx": page.width_px,
        "heightPx": page.height_px,
        "visualMetrics": rendered_visual_metrics(rendered_page),
    }
