# Early-Adopter Native-Text Review Checkpoint

Status: required when early-adopter logbooks enter ingestion

Selective native-text routing is active under
`active_controlled_fixture_gate_v1`. The controlled fixtures prove that the
router, parser, and Textract fallback behave as designed; they do not establish
that native-text routing is production-proven across real customer PDFs.

## Required Review

For the first early-adopter uploads, every page routed to `pdf_native_text`
must be reviewed against its canonical 300-DPI page before the native-text gate
is considered production-proven. Scanned, handwritten, mixed, degraded, or
uncertain pages remain Textract-routed.

Reviewers must check:

- no visible text, stamps, annotations, signatures, or values were omitted;
- reading order and entry separation match the page;
- dates, tach, Hobbs, total time, AD references, part numbers, and credentials
  are preserved exactly or remain unresolved;
- every accepted structured field points to drawable source evidence;
- absent or ambiguous values remain null rather than being inferred; and
- the original PDF and canonical render remain available and unchanged.

Record the route and activation ID, source and canonical hashes, native
reliability measurements, extractor/version, structured validation result,
review disposition, edited fields, unresolved fields, and review duration.

## Production-Proof Gate

Report the checkpoint as:

- `X passed out of Y native-routed early-adopter pages`;
- native bypass count and Textract-routed count;
- page-level failure reasons and corrections; and
- accepted-field accuracy, null preservation, evidence coverage, and median
  review time.

The initial checkpoint requires review of every available native-routed page
until at least 10 genuine early-adopter native pages have been reviewed. It
passes only with:

- 100% correct routing;
- zero visible or structured information-loss failures;
- 100% evidence coverage for accepted fields; and
- no unsupported value accepted as verified.

Any critical omission or unsafe route fails the checkpoint. Pause native
bypass, route affected and subsequent uncertain pages to Textract, preserve the
failure as an approved regression fixture, refine the provider-neutral gate,
and rerun all frozen routing regressions before reactivation.

Early-adopter pages may enter a benchmark only with explicit approval,
per-page hashes, reviewed ground truth, and account/aircraft attribution. Do
not consume the frozen full-ingestion or ingestion/AD holdout partitions for
native-text calibration.

The growing approved corpus may later support a separate Textract Custom
Queries/adapter experiment when recurring document families and labeled field
failures exist. Keep adapter training/test data separate from the frozen
holdouts, and do not interpret adapter output as improved general handwriting
recognition.
