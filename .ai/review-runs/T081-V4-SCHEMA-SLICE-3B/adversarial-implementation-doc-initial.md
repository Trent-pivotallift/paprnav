# D1-D4 Pre-persistence Implementation Review

Verdict: FAIL.

- Packet SHA-256: `c9ca616ba73c276a0174431090c253e0151630e5771536a36ac734c5fa0f998a`
- Reviewer: Codex runtime `/root/v4_s3b_design_adversary`
- Mode: independent, read-only, bounded pre-persistence review
- Base: `9ad410b`
- Independent host gate: 70 passed

## D-IMPL-001 — High

`verify_document_family` rebuilt its expected graph from the supplied family's
own proposal/projection IDs. A fully and consistently restamped foreign family
therefore passed. Trusted expected root identities must be explicit verifier
inputs and complete proposal/projection restamps must fail.

## D-IMPL-002 — High

Document and evidence ordinals enumerated submission order even though both are
canonical sets. Reversed valid input produced pointers/ordinals/hashes that
disagreed with source c14n-2 and the common-mode oracle accepted them. The
builder must independently establish canonical set order.

## D-IMPL-003 — High

Only the root document count was bounded. A 2,001-key nested evidence set was
accepted and allocated, and forged parents lacked an applicable aggregate
resource check. Every D-family array and the total source-node budget must be
checked before row allocation.

## D-IMPL-004 — Medium

The builder imported only the row domain from the generated mapping and
duplicated selectors, types, parent/ordinal rules, owner kinds, evidence
purposes, unions, and child relationships. The generated contract must drive
construction metadata or an independent exhaustive parity oracle must bind all
handwritten rules.

All six document types, D2/D3 union states, D4 unknown-only behavior, ordinary
identities/hashes, child FKs, and standard mutations otherwise passed. No
persistence omission was treated as a defect.
