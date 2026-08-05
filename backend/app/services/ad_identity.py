from __future__ import annotations

import re
from dataclasses import dataclass


AD_NUMBER_PATTERN = re.compile(
    r"\b(?:AD\s*)?((?:\d{4}|\d{2})-\d{2}-\d{2})(?:\s*(R\d+))?\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ADIdentity:
    canonical_number: str
    revision: str | None
    source_number: str


def parse_ad_identity(value: str | None) -> ADIdentity | None:
    if not value:
        return None
    match = AD_NUMBER_PATTERN.search(value.strip())
    if not match:
        return None
    base = match.group(1).upper()
    year, amendment, sequence = base.split("-")
    if len(year) == 2:
        year_number = int(year)
        year = str(2000 + year_number if year_number <= 39 else 1900 + year_number)
    canonical = f"{year}-{amendment}-{sequence}"
    revision = match.group(2).upper() if match.group(2) else None
    source_number = f"{canonical} {revision}" if revision else canonical
    return ADIdentity(
        canonical_number=canonical,
        revision=revision,
        source_number=source_number,
    )


def normalize_ad_number(value: str | None) -> str | None:
    identity = parse_ad_identity(value)
    return identity.canonical_number if identity else None
