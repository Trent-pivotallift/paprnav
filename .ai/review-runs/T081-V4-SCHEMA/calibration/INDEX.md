# T081 V4 source-complete calibration index

Status: design evidence only; no publication or implementation authority  
Domain contract: `.ai/AD_EXTRACTION_DOMAIN_CONTRACT.md` version 1.1  
Method: retained bytes, page-text extraction, and rendered-page comparison  

These packets describe reviewed semantics without choosing final JSON or SQL
field names. Exact source clauses are defined once as evidence fragments and
referenced by key. A packet can be source-complete while still failing closed
for automation because the official source is internally inconsistent or an
incorporated service bulletin is unavailable.

## Source integrity

| Packet | Retained source | SHA-256 | Pages | Rule pages reviewed | Result |
| --- | --- | --- | ---: | --- | --- |
| 2024-14-03 | `asd_63da3892cf8b4124b49e4066c57858a0` / `2024-15529.pdf` | `c7be1903331497057fb55faf9ed5994e61774d8acd287cbbc1cb0da5df423b89` | 5 | PDF 1-5; rule 1-5 | PASS |
| 2011-10-09 | `asd_dca1a807cdab483bbb876bfac5af99b7` / `2011-10988.pdf` | `cdcf75940451488e47858bd49c40615803325652ef3143d0df4178a95fe577fe` | 8 | PDF 4-8; rule 4-8 | PASS |
| 2002-13-04 | `asd_2c509af5b8df4eb2aa1cbc2f2563d54d` / `02-16174.pdf` | `6abbb7724df98bf571ab84e9d58b18f5ef87a0e89aa29817670c17f4461714b7` | 3 | PDF 1-3; rule 1-3 | PASS, source conflict recorded |
| 98-17-11 | `asd_9e7cba005b4c4529a699537f4c64940c` / `FR-1998-08-20.pdf` | `e86e204d59ad3464f31aac3945b73b03ad60adff6989ec3702a99f2d2fa06374` | 248 | PDF 16-23; FR 44545-44552 | PASS |
| 2008-26-10 | `asd_37922ee632e24a23a5f0ecd1aa4809fe` / `E8-30465.pdf` | `177c3ed17897931c0dcb902e2e867fdc7348526441d2885f26f80974402e201f` | 6 | PDF 1-6; rule 2-6 | PASS |
| 2008 correction | `asd_3c7aa0ef184646e2b32b1171e44b4f7a` / `2010-28579.pdf` | `676a282adba0fea1ef7ddb87787ce85746ea8eb08b43ac28cf059f7ccff39db2` | 2 | PDF 1-2; correction 1-2 | PASS |

## Packet disposition

| AD | Source-complete semantics | Automation eligibility | Fail-closed reason |
| --- | --- | --- | --- |
| [2024-14-03](2024-14-03.md) | Yes; human paired review complete | Eligible after design and implementation gates | Serial number is not an applicability criterion. Garmin bulletin is optional and not incorporated; its unavailable contents do not supply structured facts. |
| [2011-10-09](2011-10-09.md) | Yes; human paired review complete | Eligible after design and implementation gates | Recurring completion must record the completed action set, date, and aircraft TIS; actual next-due values require human review. |
| [2002-13-04](2002-13-04.md) | Yes; human paired review complete | Candidate-only | Applicability says `99110001 through 9912999`; actions say `99110001 through 99129999`. Twenty-seven source-cited airframe models are non-exhaustive search hints, not controlling applicability. |
| [98-17-11](1998-17-11.md) | Yes; human paired review complete | Eligible after design and implementation gates; aircraft-specific record review may be required | Engine/crankshaft evidence belongs to the component logbook. If reviewed repair provenance cannot be determined, the rule itself requires compliance. |
| [2008-26-10](2008-26-10.md) | Yes across rule and correction; human paired review complete | Candidate-only for method verification | All 182 corrected model rows and rule/correction evidence pairs are accepted. Four incorporated service bulletins are identified but not retained; dependent method detail fails closed. No AD-level AMOC language is treated as aircraft-specific use. |

## Domain-pattern coverage matrix

| Domain pattern | 2024 | 2011 | 2002 | 1998 | 2008 + correction |
| --- | :---: | :---: | :---: | :---: | :---: |
| Broad model table with shared condition | Proved | Proved | - | - | Proved |
| Engine/component applicability | Appliance/STC | - | Engine + magneto | Engine + crankshaft repair | Installed valve |
| Serial/part scope | Not applicable—serial is not an applicability criterion | All serials | Conflicting serial range | Work-order/engine serial table | P/N and all aircraft serials |
| Historical installation/repair period | - | - | - | Proved | Proved |
| Conditional branches | - | Proved | Proved | Proved | Proved |
| Alternative actions | Permitted software method | - | - | Inspect or remove; rework or replace | Inspect or temporary placard |
| One-time timing | Proved | - | Proved | Proved | Proved |
| Recurrence / whichever-first | - | Proved | - | - | Whichever-first only |
| Whichever-later | - | - | - | - | Proved |
| Before-further-flight action | - | Proved | - | - | Proved |
| Terminating/non-terminating effect | - | Explicit non-termination | Replacement ends immediate obligation | No-further-action branches | Temporary placard removed after inspection |
| Installation prohibition | Proved | - | Proved | - | Proved |
| Service information | Optional, not incorporated | None | Informational bulletin | Manuals/FAA-approved data | Four incorporated bulletins |
| General AMOC provision | Proved | Proved; prior AMOCs carried | Proved | Proved | Proved; prior AMOCs carried |
| Supersession/related AD | - | Supersedes 87-20-03 R2 | Supersedes emergency 2000-11-51 | Cross-reference to 97-26-17 | Relates to 98-01-01 and 2008-10-02 |
| Authoritative correction | - | - | Source contradiction, not correction | - | Proved |
| Actual aircraft-specific AMOC use | Not present | Not present | Not present | Not present | Not present |

## Supporting-evidence calibration gate

The five retained AD packets do **not** contain an actual aircraft-specific
approved AMOC use. They prove only AD-level AMOC authority and two cases where
prior AD AMOCs remain approved. They also do not prove a retained incorporated
service bulletin. These are administrator-ingested supporting-evidence types,
not artifacts that may be invented to complete an AD packet.

For the initial V4 design gate, the shortlist and structural workflow must
instead prove:

| Scenario | Required state before review | Required authorized transition | Prohibited result |
| --- | --- | --- | --- |
| Referenced bulletin has no retained bytes | Identity/access retained; dependent semantics `unknown` and candidate-only | Scoped administrator supplies original bytes, source/issuer/acquisition/access attribution; server stores immutable bytes and SHA-256; independent human admits exact identity/revision/scope | No unseen method detail, compliance, due value, terminating credit, or released actionability |
| Bulletin bytes retained but identity/authenticity/revision unverified | Quarantined/unverified and candidate-only | Human verifies retained hash, issuer, identity, revision, completeness, and applicability; append-only signoff creates a new signed input version | Upload alone cannot become actionable |
| Aircraft record mentions an AMOC without complete approval evidence | Customer label **possible AMOC—unverified**; candidate-only | Scoped administrator retains immutable approval bytes/source attribution; human verifies authenticity, approval reference, conditions, aircraft/configuration binding, method, and revised timing | General AMOC authority or a logbook mention grants no compliance/timing/termination credit |
| Signed supporting evidence is replayed unchanged | Existing reviewed result remains bound to identical input/version hashes | Deterministic recalculation reproduces the assessment without new review | Replay must not manufacture a new authoritative decision |
| Supporting evidence bytes, scope, or signed input changes | Dependent assessments/signoffs become stale | New attributable human review where the domain contract requires it | Old actionability or recurring due signoff cannot survive changed inputs |

When a real incorporated service bulletin or real aircraft-specific AMOC-use
record is later lawfully obtained and reviewed, its source-complete packet is
added as a regression fixture. Until then, the initial gate claims only absence/
unverified fail-closed and workflow coverage—not positive real-artifact
coverage.

## Integrity checks

- Retained-file existence and SHA-256: 6 passed out of 6.
- PDF page-count and rule-identity inspection: 6 passed out of 6.
- Gold-packet evidence-key resolution: see repository verification; expected 5 passed out of 5.
- Source-contained AD domain patterns: 17 passed out of 17.
- Supporting-evidence absence/unverified and structural workflow scenarios: 5
  specified out of 5; executable implementation verification remains future
  work.
- Future positive retained-bulletin and actual verified AMOC-use regression
  fixtures: 0 available out of 2; not required for the initial design gate and
  not represented as passed.
