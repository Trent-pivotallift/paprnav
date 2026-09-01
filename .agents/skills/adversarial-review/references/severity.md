# Finding severity and closure

- **Blocker:** can cause unsafe or unauthorized behavior, incorrect regulatory
  state, data loss/corruption, an invalid migration, or makes the claimed review
  impossible. Must close before the gate passes.
- **High:** material correctness, security, privacy, audit, availability, or
  operability defect. Fix or explicitly accept with an accountable owner.
- **Medium:** meaningful gap with bounded impact or missing regression proof.
- **Low:** localized robustness, maintainability, or clarity issue.

A finding is `closed` only after an independent reviewer checks the fix and its
verification evidence. `rejected_finding` requires evidence disproving the
claim. `accepted_risk` requires owner and rationale. Deferral does not reduce
severity and cannot bypass a blocker gate.
