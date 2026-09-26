# Initial implementation review recording delta

The immutable initial implementation review correctly records the packet the
reviewer inspected:
`1cd0d961c97c840d2803b1ed43bb9f60aa390b19dc73b45e5a460e211881b1b1`.
The corresponding `reviews.json` entry records
`d672c75eae8a2fbcb73363fa610b4be59bd893eac5e926a887dd79db7c2a527b`.

This is a coordinator recording flaw, not evidence that the reviewer inspected
the later fingerprint. After the reviewer returned, the coordinator added
D004-D006 to `findings.json` and rebuilt the packet before invoking
`record-review.py`. The packet fingerprint includes review-input bytes,
including `findings.json`, so that ledger update changed the fingerprint even
though the 19 implementation scope paths were unchanged at that point.
`record-review.py` then accurately recorded the current rebuilt packet, but not
the immutable report's reviewed fingerprint.

The historical FAIL remains useful as finding provenance but is not treated as
an attestation to `d672c...`. It is preserved unchanged. Closure does not depend
on that failed review for current-source approval: the complete remediation-3
implementation review independently passed the full current parent/child scope,
the exact locked image, and the final packet fingerprints recorded in the later
PASS entries. The final closure reviewer re-attests this explanation and the
fresh current closure packet.

No historical review entry or report was rewritten.
