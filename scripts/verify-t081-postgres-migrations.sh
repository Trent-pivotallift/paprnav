#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
backend_dir="$repo_root/backend"
verify_db="paprnav_t081_verify_$$"
database_url="postgresql+psycopg://paprnav_user:paprnav_password@db:5432/$verify_db"

if [[ ! "$verify_db" =~ ^paprnav_t081_verify_[0-9]+$ ]]; then
  printf 'Refusing unvalidated verification database name: %s\n' "$verify_db" >&2
  exit 1
fi

cleanup() {
  docker compose exec -T db dropdb --if-exists -U paprnav_user "$verify_db" >/dev/null
}
trap cleanup EXIT

cd "$backend_dir"
docker compose exec -T db createdb -U paprnav_user "$verify_db"

run_alembic() {
  docker compose run --rm -T -e DATABASE_URL="$database_url" api alembic "$@"
}

run_alembic upgrade head
run_alembic downgrade 20260822_0023

# A terminal/attributed v3 review with a null decision_output must still retain
# an immutable pre-repair snapshot when 0024 conservatively reopens it.
docker compose exec -T db psql -v ON_ERROR_STOP=1 -U paprnav_user -d "$verify_db" <<'SQL'
INSERT INTO ad_discovery_records (
  id, federal_register_document_number, title, api_snapshot, content_hash,
  classification, classification_confidence, classification_reason,
  classifier_name, classifier_version
) VALUES (
  'adr_t081_null_decision', 'T081-NULL-DECISION', 'T081 migration fixture',
  '{}'::json, repeat('a', 64), 'ad_candidate', 1.0, 'fixture', 'fixture', '1'
), (
  'adr_t081_nonempty', 'T081-NONEMPTY', 'T081 nonempty AMOC fixture',
  '{}'::json, repeat('c', 64), 'ad_candidate', 1.0, 'fixture', 'fixture', '1'
), (
  'adr_t081_partial', 'T081-PARTIAL', 'T081 partial envelope fixture',
  '{}'::json, repeat('d', 64), 'ad_candidate', 1.0, 'fixture', 'fixture', '1'
);
INSERT INTO airworthiness_directives (
  id, discovery_record_id, ad_number, title, status, source_content_hash,
  extraction_status, review_status
) VALUES (
  'ad_t081_null_decision', 'adr_t081_null_decision', '2026-81-01',
  'T081 migration fixture', 'candidate', repeat('a', 64), 'complete', 'approved'
), (
  'ad_t081_nonempty', 'adr_t081_nonempty', '2026-81-02',
  'T081 nonempty AMOC fixture', 'candidate', repeat('c', 64), 'complete', 'approved'
), (
  'ad_t081_partial', 'adr_t081_partial', '2026-81-03',
  'T081 partial envelope fixture', 'candidate', repeat('d', 64), 'complete', 'approved'
);
INSERT INTO ad_extractions (
  id, directive_id, provider_name, provider_version, schema_version,
  input_content_hash, status, confidence, output, citations, raw_response
) VALUES (
  'adx_t081_null_decision', 'ad_t081_null_decision', 'fixture', '1',
  'ad_extraction_v3', repeat('b', 64), 'approved', 1.0,
  '{"adNumber":"2026-81-01","requirements":[],"applicabilityGroups":[]}'::json,
  '[]'::json, '{}'::json
), (
  'adx_t081_nonempty', 'ad_t081_nonempty', 'fixture', '1',
  'ad_extraction_v3', repeat('c', 64), 'approved', 1.0,
  '{"adNumber":"2026-81-02","requirements":[],"applicabilityGroups":[],"amocProvisions":[{"authority":"FAA","method":"existing approved AMOC"}]}'::json,
  '[]'::json, '{}'::json
), (
  'adx_t081_partial', 'ad_t081_partial', 'fixture', '1',
  'ad_extraction_v3', repeat('d', 64), 'approved', 1.0,
  '{"adNumber":"2026-81-03","requirements":[],"applicabilityGroups":[],"amocProvisions":[]}'::json,
  '[]'::json, '{}'::json
);
INSERT INTO ad_extraction_reviews (
  id, extraction_id, status, proposed_output, decision_output, decision,
  reviewer_user_id, notes, reviewed_at
) VALUES (
  'arv_t081_null_decision', 'adx_t081_null_decision', 'approved',
  '{"adNumber":"2026-81-01","requirements":[],"applicabilityGroups":[]}'::json,
  NULL, 'approved', NULL, 'legacy terminal review', now()
), (
  'arv_t081_nonempty', 'adx_t081_nonempty', 'approved',
  '{"adNumber":"2026-81-02","requirements":[],"applicabilityGroups":[],"amocProvisions":[{"authority":"FAA","method":"existing approved AMOC"}]}'::json,
  '{"adNumber":"2026-81-02","requirements":[],"applicabilityGroups":[],"amocProvisions":[{"authority":"FAA","method":"existing approved AMOC"}]}'::json,
  'approved', NULL, 'preserve nonempty AMOC', now()
), (
  'arv_t081_partial', 'adx_t081_partial', 'edited',
  '{"adNumber":"2026-81-03","requirements":[],"applicabilityGroups":[]}'::json,
  '{"adNumber":"2026-81-03","requirements":[],"applicabilityGroups":[],"amocProvisions":[]}'::json,
  'edited', NULL, 'partial envelope state', now()
);
SQL
run_alembic upgrade 20260823_0024

repair_snapshot="$({
  docker compose exec -T db psql -v ON_ERROR_STOP=1 -U paprnav_user -d "$verify_db" -Atc \
    "select count(*) || ':' || coalesce(max(metadata_json::jsonb ->> 'repairActor'), '') || ':' || coalesce(bool_and(decision_output is null), false) from ad_extraction_review_decisions where review_id = 'arv_t081_null_decision' and event_type = 'migration_repair_snapshot';"
} | tr -d '[:space:]')"
if [[ "$repair_snapshot" != "1:alembic:20260823_0024:true" ]]; then
  printf 'Null-decision repair snapshot was not preserved: %s\n' "$repair_snapshot" >&2
  exit 1
fi
review_reopened="$({
  docker compose exec -T db psql -v ON_ERROR_STOP=1 -U paprnav_user -d "$verify_db" -Atc \
    "select status || ':' || coalesce(decision, 'null') || ':' || coalesce(reviewed_at::text, 'null') from ad_extraction_reviews where id = 'arv_t081_null_decision';"
} | tr -d '[:space:]')"
if [[ "$review_reopened" != "pending:null:null" ]]; then
  printf 'Fixture review was not conservatively reopened: %s\n' "$review_reopened" >&2
  exit 1
fi
cohort_result="$({
  docker compose exec -T db psql -v ON_ERROR_STOP=1 -U paprnav_user -d "$verify_db" -Atc \
    "select count(*) || ':' || count(*) filter (where review.status = 'pending' and review.decision is null and review.reviewed_at is null) || ':' || count(*) filter (where extraction.status = 'needs_review' and extraction.raw_response::jsonb ->> 'amocEnvelopeOrigin' = 'migration_repair_pending') from ad_extraction_reviews review join ad_extractions extraction on extraction.id = review.extraction_id where extraction.id in ('adx_t081_null_decision','adx_t081_nonempty','adx_t081_partial');"
} | tr -d '[:space:]')"
if [[ "$cohort_result" != "3:3:3" ]]; then
  printf 'Full ambiguous cohort was not conservatively reopened: %s\n' "$cohort_result" >&2
  exit 1
fi
payload_result="$({
  docker compose exec -T db psql -v ON_ERROR_STOP=1 -U paprnav_user -d "$verify_db" -Atc \
    "select (not (empty_extraction.output::jsonb ? 'amocProvisions'))::text || ':' || (not (partial_review.proposed_output::jsonb ? 'amocProvisions'))::text || ':' || (nonempty_extraction.output::jsonb #>> '{amocProvisions,0,method}') || ':' || (nonempty_review.proposed_output::jsonb #>> '{amocProvisions,0,method}') from ad_extractions empty_extraction cross join ad_extractions nonempty_extraction cross join ad_extraction_reviews nonempty_review cross join ad_extraction_reviews partial_review where empty_extraction.id = 'adx_t081_partial' and nonempty_extraction.id = 'adx_t081_nonempty' and nonempty_review.id = 'arv_t081_nonempty' and partial_review.id = 'arv_t081_partial';"
} | tr -d '[:space:]')"
if [[ "$payload_result" != "true:true:existingapprovedAMOC:existingapprovedAMOC" ]]; then
  printf 'Empty/nonempty/partial AMOC payload repair was incorrect: %s\n' "$payload_result" >&2
  exit 1
fi
snapshot_result="$({
  docker compose exec -T db psql -v ON_ERROR_STOP=1 -U paprnav_user -d "$verify_db" -Atc \
    "select count(*) || ':' || count(*) filter (where decision_output is null) || ':' || count(*) filter (where decision_output::jsonb #>> '{amocProvisions,0,method}' = 'existing approved AMOC') || ':' || count(*) filter (where decision_output::jsonb -> 'amocProvisions' = '[]'::jsonb) from ad_extraction_review_decisions where review_id in ('arv_t081_null_decision','arv_t081_nonempty','arv_t081_partial') and event_type = 'migration_repair_snapshot';"
} | tr -d '[:space:]')"
if [[ "$snapshot_result" != "3:1:1:1" ]]; then
  printf 'Partial/nonempty/null decision snapshots were not preserved: %s\n' "$snapshot_result" >&2
  exit 1
fi
run_alembic upgrade 20260823_0024
rerun_result="$({
  docker compose exec -T db psql -v ON_ERROR_STOP=1 -U paprnav_user -d "$verify_db" -Atc \
    "select count(*) || ':' || count(*) filter (where event_type = 'migration_repair_snapshot') from ad_extraction_review_decisions where review_id in ('arv_t081_null_decision','arv_t081_nonempty','arv_t081_partial');"
} | tr -d '[:space:]')"
if [[ "$rerun_result" != "3:3" ]]; then
  printf 'Repair rerun was not idempotent: %s\n' "$rerun_result" >&2
  exit 1
fi
if run_alembic downgrade 20260822_0021 >/dev/null 2>&1; then
  printf '0024 downgrade unexpectedly accepted live immutable decision history\n' >&2
  exit 1
fi
still_at_head="$(run_alembic current | tr -d '\r')"
if [[ "$still_at_head" != *"20260823_0024"* ]]; then
  printf 'Guarded downgrade changed revision unexpectedly: %s\n' "$still_at_head" >&2
  exit 1
fi
docker compose exec -T db psql -v ON_ERROR_STOP=1 -U paprnav_user -d "$verify_db" <<'SQL'
DELETE FROM ad_extraction_review_decisions WHERE review_id = 'arv_t081_null_decision';
DELETE FROM ad_extraction_review_decisions WHERE review_id IN ('arv_t081_nonempty', 'arv_t081_partial');
DELETE FROM ad_extraction_reviews WHERE id IN ('arv_t081_null_decision', 'arv_t081_nonempty', 'arv_t081_partial');
UPDATE ad_extractions
SET raw_response = '{"amocEnvelopeOrigin":"llm_provider"}'::json
WHERE id IN ('adx_t081_null_decision', 'adx_t081_nonempty', 'adx_t081_partial');
SQL
if run_alembic downgrade 20260822_0021 >/dev/null 2>&1; then
  printf '0024 downgrade unexpectedly accepted origin-marked v3 extraction\n' >&2
  exit 1
fi
still_at_head="$(run_alembic current | tr -d '\r')"
if [[ "$still_at_head" != *"20260823_0024"* ]]; then
  printf 'V3 guard changed revision unexpectedly: %s\n' "$still_at_head" >&2
  exit 1
fi
docker compose exec -T db psql -v ON_ERROR_STOP=1 -U paprnav_user -d "$verify_db" <<'SQL'
DELETE FROM ad_extractions WHERE id IN ('adx_t081_null_decision', 'adx_t081_nonempty', 'adx_t081_partial');
DELETE FROM airworthiness_directives WHERE id IN ('ad_t081_null_decision', 'ad_t081_nonempty', 'ad_t081_partial');
DELETE FROM ad_discovery_records WHERE id IN ('adr_t081_null_decision', 'adr_t081_nonempty', 'adr_t081_partial');
SQL
run_alembic downgrade 20260822_0021

parent_index="$({
  docker compose exec -T db psql -U paprnav_user -d "$verify_db" -Atc \
    "select indexdef from pg_indexes where indexname = 'uq_ad_target_applicability';"
} | tr -d '[:space:]')"
for column in directive_id target_id source_publication_id applicability_basis applicability_group_key; do
  if [[ "$parent_index" != *"$column"* ]]; then
    printf 'Missing %s from reconstructed 0021 applicability identity: %s\n' "$column" "$parent_index" >&2
    exit 1
  fi
done
if [[ "$parent_index" == *"source_extraction_id"* ]]; then
  printf '0021 parent constraint unexpectedly contains source_extraction_id: %s\n' "$parent_index" >&2
  exit 1
fi

run_alembic downgrade 20260809_0020
run_alembic upgrade head
docker compose run --rm -T -e DATABASE_URL="$database_url" api \
  python -m app.scripts.verify_ad_review_concurrency
docker compose run --rm -T -e DATABASE_URL="$database_url" api \
  python -m app.scripts.verify_ad_staging_concurrency
docker compose run --rm -T -e DATABASE_URL="$database_url" api \
  python -m app.scripts.verify_ad_correction_workflow
docker compose run --rm -T \
  -e PYTHONPATH=/app \
  -e PAPRNAV_TEST_POSTGRES_URL="$database_url" \
  api pytest -q tests/test_ad_evidence_postgres.py
current_revision="$(run_alembic current | tr -d '\r')"
if [[ "$current_revision" != *"20260830_0025"* ]]; then
  printf 'Unexpected final migration revision: %s\n' "$current_revision" >&2
  exit 1
fi

printf '14 passed out of 14\n'
