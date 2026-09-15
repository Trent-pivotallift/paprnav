# T081 V4 Schema Slice 4 implementation closure review 1

Outcome: **FAIL**  
Reviewer runtime: `/root/v4_s4_design_adversary`  
Exact packet SHA-256: `1a7385408bd7b6ae26378037d1b313c4c2735b82891eeb84492494927a4c6c37`  
Base: `4840a0b4bc5d7334ddcf51a80e39c8fa84b7b0c2`

## T081-V4-S4-IMPL-B-001 — CLOSED

SQL now validates nested value types, digest encoding, required/forbidden
fields, actual evidence absence, evidence heads, selected projection identity,
and directive ownership. Fully resealed malformed-digest, nonverified-source,
and cross-directive variants are covered. Positive branch tests verify
SQL-accepted observations against Python. The independent 77-test PostgreSQL
closure run passed.

## T081-V4-S4-IMPL-H-001 — OPEN

The original fragment/relationship cycle is fixed and six real
two-administrator interleavings pass. A residual remains in inherited SQL.

Invariant: cooperating application and direct-SQL writers must use the same
authorization lock order.

Evidence:

- final-schema `paprnav_v4_validate_submission()` still locks membership before
  user, while review SQL locks user before membership;
- final-schema `paprnav_v4_validate_app_materialization_request()` similarly
  locks membership before user;
- the passing interleavings use application writers that pre-acquire user
  first, so they do not cover these direct-SQL trigger paths.

Impact: a same-actor review may hold user U while a direct-SQL writer holds
membership M, producing a U/M cycle.

Required closure: replace both inherited guards in 0029 with user-before-
membership ordering, restore prior definitions on downgrade, and force direct-
SQL-versus-review interleavings without application authorization pre-locks.

## T081-V4-S4-IMPL-H-002 — CLOSED

Expected retained-storage failures now have a dedicated allowlisted boundary
outside structural validation. Tests cover observation through rejection and
prove unexpected programming/database/provider errors propagate.

## T081-V4-S4-IMPL-M-001 — OPEN

Row caps, limit-plus-one checks, source caching, and batched lookups do not yet
bound aggregate bytes. A legal 1,000-draft allocation-light probe measured
approximately 1.98 GB before ORM/driver/parsing overhead because annotations
and request blobs are repeated in draft/event rows.

Required closure: enforce a practical aggregate per-case byte/work budget in
service admission, SQL commit validation, and read preflight before loading
blobs. Add exact-boundary, fully resealed direct-SQL overflow, and query/work
budget tests while retaining request/rejection capacity.

## Independent verification

- focused host API/service: 73 passed;
- PostgreSQL observation/migration/concurrency/lifecycle: 77 passed;
- `git diff --check`: passed;
- packet hash remained unchanged.

The reviewer remained read-only. Rejection-only scope and affirmative-authority
isolation remain intact.
