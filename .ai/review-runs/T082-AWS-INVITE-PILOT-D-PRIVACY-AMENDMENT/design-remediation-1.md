# Privacy design remediation 1

Date: 2026-09-19. Builder evidence only; no implementation or finding closure.
Authority: `adversarial-design-initial.md`, PRIV-001/PRIV-002 in the child ledger,
and the amended `decision.md`. The prior review report remains immutable.

## Design changes

- PRIV-001: connection-close authority requires current captured cycle and
  transport identity plus no confirmed successful final send, checked without
  an intervening await. Completed/non-current requests cannot close a successor
  transport. The decision distinguishes confirmed final-send completion from
  Uvicorn's earlier `response_complete` flag. It specifies current incomplete,
  completed and non-current cancellation, plain/pure-grouped/mixed cancellation,
  and overlapping pipelined-task evidence.
- PRIV-002: disconnect observation is limited to receive/send/drain; no new
  watcher is introduced. Unrelated awaits may remain pending. Uvicorn owns
  graceful-shutdown task cancellation, followed by the local cooperative-task
  completion bound. The oracle records initial pending state and deadline
  results before a separate cleanup phase; cleanup cannot manufacture a pass.
- The locked-image oracle has an explicit backend-only module and command
  rooted at `/app`, with no `/infra`, frontend or repository-parent dependency.
  Runtime DB-outage assertions are separated from the existing static gates.

The approved logging flag/startup ownership, conditional evidence delivery,
locked-image gate, rollback and Package E limitations remain. D005/D006 remain
preserved. Only the child decision and this new note were edited; no application,
test, ledger, attestation, state, parent artifact or prior report was changed.

## Verification and gate

This is a source/review-grounded design amendment. No runtime test or image build
is claimed. The new expected-state matrix is work for the implementation after
independent design PASS. The coordinator must obtain independent re-review;
implementation remains paused.

## Model routing

- Builder runtime: `/root/t082_package_d_privacy_amendment_design`.
- Role: design remediation builder; requested `gpt-6-astra`, `xhigh`.
- Actual model: `model not exposed by runtime`; actual effort: `effort not exposed`.
- Trigger: PRIV-001/PRIV-002 after independent review of the third-loop privacy
  architecture reassessment; interacting cycle ownership and liveness guarantees.
- Initial reviewer: `/root/t082_package_d_privacy_review_2`; requested
  `gpt-6-astra`, `xhigh`; actual model `model not exposed by runtime`, actual
  effort `effort not exposed`. That review remains FAIL pending re-review.
