# DRS Bulk ZIP Validation

One-shot validation for whether the FAA DRS bulk ZIP can be treated as a comprehensive Airworthiness Directive source for a closed historical window.

## Setup

Use an isolated virtual environment from this directory:

```bash
cd tools/drs_zip_validation
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## Run

Default comparison window is calendar year 2024:

```bash
python validate_drs_zip.py
```

Optional flags:

```bash
python validate_drs_zip.py --start-date 2024-01-01 --end-date 2024-12-31
python validate_drs_zip.py --force-download
python validate_drs_zip.py --no-cache
python validate_drs_zip.py --bulk-zip-url "https://drs.faa.gov/path/to/ADFinalRulesEmergencyADs_05312026.zip"
```

Use `--bulk-zip-url` when Playwright cannot discover the DRS download control but a human has copied the current ZIP URL from the browser. In current DRS behavior, the ZIP may be delivered as a browser download without exposing a stable reusable HTTP URL; the script saves that download under `data/drs_bulk.zip`.

## Outputs

The script writes:

- `findings.md`: human-readable report with inventory, coverage, gaps, and verdict.
- `data/drs_bulk.zip`: downloaded DRS ZIP.
- `data/bulk_zip_url.txt`: discovered ZIP URL.
- `data/fr_responses/*.json`: cached Federal Register pages and detail responses.
- `data/fr_set.json`: normalized AD numbers from Federal Register.
- `data/zip_set.json`: normalized AD numbers from the ZIP.
- `data/zip_set_window.json`: ZIP AD numbers filtered to the comparison year/window.

The current DRS bulk ZIP has been observed as a single Access database (`.accdb`). The script extracts normalized AD identifiers from that database for source-coverage validation. It does not parse row-level Access publication dates; the year/window file is an AD-number-year surrogate.

## Expected Runtime

Runtime depends mostly on the ZIP size and whether Federal Register AD numbers are present in titles. If titles omit AD numbers, the script fetches Federal Register document details and XML at no more than one request per second. Expect several minutes.

## Interpretation

The script prints and writes one of these verdicts based on full ZIP source coverage against the Federal Register AD set:

- `PASS`: coverage is at least 98%.
- `CONDITIONAL`: coverage is 85% to 97.9%.
- `FAIL`: coverage is below 85%.

If DRS blocks Playwright, the ZIP URL cannot be found, Federal Register returns no AD documents, or ZIP extraction yields an implausibly small AD set, the script fails loudly and writes a failure `findings.md`.

This is validation code only. Do not import it into the production backend pipeline.
