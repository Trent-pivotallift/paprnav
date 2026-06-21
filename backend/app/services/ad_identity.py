from __future__ import annotations

import re


AD_NUMBER_PATTERN = re.compile(r"\b(?:AD\s*)?((?:\d{4}|\d{2})-\d{2}-\d{2})\b", re.IGNORECASE)


def normalize_ad_number(value: str | None) -> str | None:
    if not value:
        return None
    match = AD_NUMBER_PATTERN.search(value.strip())
    if not match:
        return None
    number = match.group(1).upper()
    year, amendment, sequence = number.split("-")
    if len(year) == 2:
        year_number = int(year)
        full_year = 2000 + year_number if year_number <= 39 else 1900 + year_number
        year = str(full_year)
    return f"{year}-{amendment}-{sequence}"
