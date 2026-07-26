from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from tempfile import NamedTemporaryFile

from PIL import Image, ImageDraw
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


OUTPUT_DIR = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "native_text"


def generate() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fixtures = {
        "pure_native": create_pure_native(OUTPUT_DIR / "pure_native.pdf"),
        "native_table": create_native_table(OUTPUT_DIR / "native_table.pdf"),
        "mixed_native_image": create_mixed(OUTPUT_DIR / "mixed_native_image.pdf"),
    }
    manifest = {
        "version": "native-routing-fixtures-v1",
        "fixtures": fixtures,
    }
    (OUTPUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )


def create_pure_native(path: Path) -> dict:
    pdf = canvas.Canvas(str(path), pagesize=letter, pageCompression=0, invariant=1)
    lines = [
        "Paprnav Controlled Native Maintenance Entry",
        "Date: 2024-05-10",
        "Tach: 1250.4  Hobbs: 1402.8  Total Time: 5400.2",
        "Completed annual inspection in accordance with 14 CFR Part 43 Appendix D.",
        "Complied with AD 2020-01-02 by inspection; no defects noted.",
        "Performer: Alex Mechanic A&P 2192007 IA",
        "Aircraft returned to service.",
    ]
    draw_lines(pdf, lines)
    pdf.save()
    return fixture_record(
        path,
        "native_text",
        lines,
        [
            {
                "entryDate": "2024-05-10",
                "tachTime": 1250.4,
                "hobbsTime": 1402.8,
                "totalTime": 5400.2,
            }
        ],
    )


def create_native_table(path: Path) -> dict:
    pdf = canvas.Canvas(str(path), pagesize=letter, pageCompression=0, invariant=1)
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(54, 744, "Paprnav Controlled Native Maintenance Table")
    rows = [
        ["Date", "Times", "Maintenance and approval"],
        ["2024-06-01", "Tach 1260.5 / Total 5410.3", "Oil and filter changed; screen inspected clean."],
        ["2024-07-15", "Tach 1288.1 / Total 5437.9", "100-hour inspection completed; returned to service."],
    ]
    x = [54, 150, 330, 558]
    y_top = 700
    row_height = 70
    pdf.setFont("Helvetica", 9)
    for row_index, row in enumerate(rows):
        y = y_top - row_index * row_height
        for index in range(4):
            pdf.line(x[index], y, x[index], y - row_height)
        pdf.line(x[0], y, x[-1], y)
        for index, value in enumerate(row):
            pdf.drawString(x[index] + 4, y - 20, value)
    pdf.line(x[0], y_top - len(rows) * row_height, x[-1], y_top - len(rows) * row_height)
    pdf.drawString(54, 450, "Performer: Taylor Technician A&P 3344556 IA")
    pdf.drawString(54, 430, "AD 2021-03-04 explicitly reviewed; not applicable.")
    pdf.save()
    expected = [value for row in rows for value in row] + [
        "Performer: Taylor Technician A&P 3344556 IA",
        "AD 2021-03-04 explicitly reviewed; not applicable.",
    ]
    return fixture_record(
        path,
        "native_text",
        expected,
        [
            {"entryDate": "2024-06-01", "tachTime": 1260.5, "totalTime": 5410.3},
            {"entryDate": "2024-07-15", "tachTime": 1288.1, "totalTime": 5437.9},
        ],
    )


def create_mixed(path: Path) -> dict:
    with NamedTemporaryFile(suffix=".png") as image_file:
        image = Image.new("RGB", (1400, 900), "white")
        drawing = ImageDraw.Draw(image)
        drawing.rectangle((10, 10, 1390, 890), outline="black", width=8)
        drawing.text((80, 150), "SCANNED IMAGE NOTE - MATERIAL CONTENT", fill="black")
        drawing.text((80, 320), "Tach 1500.5 - Magneto replaced", fill="black")
        drawing.text((80, 490), "Signed: Image-only Mechanic", fill="black")
        image.save(image_file.name)

        pdf = canvas.Canvas(str(path), pagesize=letter, pageCompression=0, invariant=1)
        draw_lines(
            pdf,
            [
                "Paprnav Controlled Mixed Maintenance Page",
                "Date: 2024-08-20",
                "Typed cover text references the scanned maintenance note below.",
                "The image contains material maintenance values and approval evidence.",
            ],
            start_y=750,
        )
        pdf.drawImage(
            ImageReader(image_file.name),
            54,
            120,
            width=504,
            height=324,
            preserveAspectRatio=True,
        )
        pdf.save()
    return fixture_record(
        path,
        "aws_textract",
        [
            "Paprnav Controlled Mixed Maintenance Page",
            "Date: 2024-08-20",
        ],
        [{"entryDate": "2024-08-20"}],
    )


def draw_lines(pdf: canvas.Canvas, lines: list[str], *, start_y: int = 750) -> None:
    pdf.setFont("Helvetica", 11)
    y = start_y
    for line in lines:
        pdf.drawString(54, y, line)
        y -= 28


def fixture_record(
    path: Path,
    expected_route: str,
    expected_text: list[str],
    expected_entries: list[dict],
) -> dict:
    data = path.read_bytes()
    return {
        "filename": path.name,
        "sha256": sha256(data).hexdigest(),
        "expectedRoute": expected_route,
        "expectedText": expected_text,
        "expectedEntryCount": len(expected_entries),
        "expectedEntries": expected_entries,
    }


if __name__ == "__main__":
    generate()
