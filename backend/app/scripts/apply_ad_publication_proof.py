import argparse
import json

from app.db.session import SessionLocal
from app.services.ad_publication_persistence import apply_publication_proof_file


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument(
        "--artifact-root",
        help="Root for content-addressed paths in the manifest; defaults to the manifest directory",
    )
    args = parser.parse_args()
    with SessionLocal() as db:
        stats = apply_publication_proof_file(
            db,
            args.manifest,
            artifact_root=args.artifact_root,
        )
        db.commit()
    print(json.dumps(stats, sort_keys=True))


if __name__ == "__main__":
    main()
