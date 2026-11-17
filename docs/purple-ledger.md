# Purple review ledger

Import completed CI reports into a local SQLite ledger to create a review queue.
The ledger retains candidate revision, effective policy, component and control
IDs. It keeps one case per revision, policy, component and rule. Reimporting an
artifact leaves existing reviews intact. Analysts record a triage label, then
export reviewed cases for the offline evaluator under a specific policy.

```sh
python -m cyberops.ledger --db local.db ingest cyberops-report.json
python -m cyberops.ledger --db local.db pending
python -m cyberops.ledger --db local.db review "$CASE_ID" --reviewer analyst --label priority
python -m cyberops.ledger --db local.db export --policy "$POLICY_SHA256" > reviewed.json
```

Use the full `effective_policy_sha256` from the source report. Produce that
report with `--candidate-revision` or the GitHub Actions gate. Use the export
as training input to the [offline replay benchmark](defensive-learning.md).
Create a separate holdout from later reviewed cases, with overlapping case IDs
excluded. Supervisors should control who can write the database and verify
report provenance before ingest. The reviewer field records an operator-supplied
label and does not authenticate the operator. Reviews are single-write through
the CLI, and direct database access must be controlled separately.

This closes the CI finding → analyst triage → offline evaluation loop. The
result is advisory. Production actions, release decisions, and model promotion
remain outside the ledger. Distributed identity, signed evidence, and a shared
service require a separate deployment trust boundary.
