from app.services.ad_identity import normalize_ad_number, parse_ad_identity


def test_ad_identity_retains_revision_while_matching_on_canonical_number() -> None:
    identity = parse_ad_identity("AD 98-21-21 R1")

    assert identity is not None
    assert identity.canonical_number == "1998-21-21"
    assert identity.revision == "R1"
    assert identity.source_number == "1998-21-21 R1"
    assert normalize_ad_number("98-21-21 R1") == "1998-21-21"
