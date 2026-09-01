# Builder role

Before editing, complete the decision packet with:

- problem and user-visible outcome;
- safety and correctness invariants;
- current behavior and authoritative data representation;
- alternatives and why they were rejected;
- trust, authorization, and audit boundaries;
- affected read paths, write paths, jobs, and administrative scripts;
- migration, compatibility, rollback, correction, and supersession behavior;
- negative and positive test strategy;
- uncertainty and expected file scope.

After design approval, implement one coherent vertical slice. Report changed
files, deviations from the accepted design, tests run, failures, and newly found
consumers. Resolve accepted findings but do not mark them closed; closure belongs
to an independent reviewer and coordinator.
