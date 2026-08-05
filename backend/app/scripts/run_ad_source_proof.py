from __future__ import annotations

import argparse

from app.services.ad_source_proof import run_drs_target_proof, write_proof_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the retained DRS target proof")
    parser.add_argument("--drs-zip", required=True)
    parser.add_argument("--airframe-results", required=True)
    parser.add_argument("--engine-results", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    manifest = run_drs_target_proof(
        drs_zip_path=args.drs_zip,
        airframe_results_path=args.airframe_results,
        engine_results_path=args.engine_results,
    )
    write_proof_manifest(manifest, args.output)
    verification = manifest["verification"]
    print(f"{verification['passed']} passed out of {verification['total']}")


if __name__ == "__main__":
    main()
