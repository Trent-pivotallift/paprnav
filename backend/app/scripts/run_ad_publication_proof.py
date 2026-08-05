from __future__ import annotations

import argparse

from app.core.config import get_settings
from app.services.ad_publication_proof import run_publication_reconciliation
from app.services.ad_source_proof import write_proof_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Reconcile target ADs with FR/GovInfo")
    parser.add_argument("--drs-zip", required=True)
    parser.add_argument("--artifact-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    settings = get_settings()
    if not settings.govinfo_api_key:
        raise SystemExit("GOVINFO_API_KEY is required")
    manifest = run_publication_reconciliation(
        drs_zip_path=args.drs_zip,
        output_root=args.artifact_root,
        govinfo_api_key=settings.govinfo_api_key,
        govinfo_base_url=settings.govinfo_base_url,
    )
    write_proof_manifest(manifest, args.output)
    verification = manifest["verification"]
    print(f"{verification['passed']} passed out of {verification['total']}")


if __name__ == "__main__":
    main()
