# Initiate a defensive feedback cycle

CyberOps can resume the same loop as CI artifacts and analyst reviews arrive.
The loop is offline, advisory, and separate from the release gate.

1. Generate a decision report using the [exposure example](enterprise-resilience.md#try-the-exposure-queue).
   Use the report's `effective_policy_sha256` as `POLICY_SHA`.
2. Initialize or resume the review queue.

   ```sh
   python -m cyberops.feedback --db feedback.db --policy "$POLICY_SHA" \
     --report /tmp/cyberops-exposure.json
   ```

3. Label each returned case using `python -m cyberops.ledger --db feedback.db review
   CASE_ID --reviewer ANALYST --label priority` or use `standard`. Labels are
   supplied by an analyst and should come from a controlled review process.
4. Rerun the cycle with separately labeled holdout cases.

   ```sh
   python -m cyberops.feedback --db feedback.db --policy "$POLICY_SHA" \
     --held-out examples/defensive-replay/held-out.json
   ```

The stages are `evidence_required`, `review_required`, `holdout_required`
and `evaluated`. Reimports are idempotent. An invalid report or a finding
from a different policy rejects the entire import batch. Each successful
evaluation records fingerprints of the reviewed training rows and the
holdout file. To add another revision, rerun with
its trusted report. Reviews train the offline evaluator, and overlapping case
IDs are rejected. The supplied holdout illustrates fallback with unfamiliar
controls. Use independently reviewed, comparable cases to measure quality.

## Validation and scope

| Requested improvement | Status |
| --- | --- |
| MARL | Offline defensive routing uses reviewed labels. Cooperative-competitive attack policies are outside scope. |
| Purple intelligence | Persistent SQLite queue and offline replay handoff verified. Distributed event streaming and signature generation are absent. |
| Scope and blast radius | The simulator has no network targets or actuation. Live target and protected-asset controls are outside the verified scope. |
| Environment wrapper | Seeded synthetic simulation works. PettingZoo and Gymnasium adapters are absent. |
| Analyst approval | The feedback cycle waits for operator labels. Authenticated inline approval and override interfaces are absent. |
| Knowledge graph | Policy-scoped ledger lookup works. A graph database and vector search are absent. |
| Exploit mutation | Outside scope. Synthetic defensive inputs are available for boundary tests. |
| Explainability | JSON reports include decisions, supporting counts and fallback reasons. No attribution dashboard is deployed. |
| Quickstart | CI findings through analyst review and offline evaluation are runnable above. Live enforcement and custom topology generation are absent. |
| CI smoke test | The pull-request workflow runs the deterministic 10-step test and validates installed entry points. Remote execution remains unverified. |

The feedback command is invoked per batch or by an enterprise scheduler. It
does not deploy a policy or run as a production worker. Keep the ledger and
artifact ingress under operator control, with provenance verification at the
artifact boundary.
