# Enterprise connector catalog

These 15 integration priorities cover CI/CD, defensive security evidence,
approved adversarial assessment results and remediation workflows. The order
reflects a suggested rollout for CyberOps.

| # | Platform | Why an enterprise would connect it | Delivery status |
| --- | --- | --- | --- |
| 1 | GitHub Actions | Run the gate on candidate revisions and retain decision artifacts | Native gate workflow shipped. Defensive producer setup is separate. |
| 2 | GitLab CI/CD | Run a required gate and retain defensive job artifacts | Portable CLI contract |
| 3 | Azure Pipelines | Enforce defensive checks in an existing release pipeline | Portable CLI contract |
| 4 | Jenkins | Gate a self-managed pipeline and archive check results | Portable CLI contract |
| 5 | CircleCI | Ingest outcomes from existing build and security jobs | Portable CLI contract |
| 6 | Buildkite | Run the gate on enterprise-managed agents | Portable CLI contract |
| 7 | Semgrep | Supply a policy result from static application analysis | Portable status input. Native parser planned. |
| 8 | Trivy | Check image, dependency or IaC policy in an upstream job | Portable status input. Native parser planned. |
| 9 | Snyk | Import an approved dependency policy outcome | Portable status input. Native parser planned. |
| 10 | Checkov | Import an IaC policy outcome from a trusted job | Portable status input. Native parser planned. |
| 11 | Gitleaks | Submit the upstream secret-scanning policy outcome | Portable status input. Raw secrets stay upstream. |
| 12 | Pentera | Import reviewed assessment disposition for a mapped control | Planned results-only integration |
| 13 | AttackIQ | Import approved control validation outcomes for Purple review | Planned results-only integration |
| 14 | Jira | Link owners and findings to remediation tickets | Planned outbound mapping |
| 15 | ServiceNow | Link gate evidence to a change or remediation record | Planned outbound mapping |

Portable means the operator invokes the CLI in the CI system and maps trusted
job outcomes to the documented contract. It does not imply a native marketplace
extension or vendor API integration. Red-team platform connections are
results-only. CyberOps does not launch or orchestrate offensive testing.

## Export defensive evidence

Run the exporter in a trusted producer job with the exact commit SHA supplied
by the CI platform. The target file must be new. Use one component per export
and supply its named checks via test artifacts or explicit statuses. Derive
explicit statuses from completed jobs so execution failures become `error`
rather than successful checks.

```sh
python3 -m cyberops.connectors --revision "$CANDIDATE_SHA" \
  --component example-service \
  --status dependency-policy pass \
  --junit guardrail-regression path/to/junit.xml \
  --output evidence.json
```

The status in this example is illustrative. The JUnit adapter returns an error
outcome for skipped or errored tests, fails when a test fails and rejects empty
or malformed reports. The exporter copies only check identifiers and outcomes.
Pass the resulting file to the gate with `--evidence` and the trusted SHA with
`--revision`. See the [evidence demo](../README.md#evaluate-ci-check-evidence).

## Rollout for a mission-critical service

1. Assign component ownership and require checks from a trusted policy branch.
2. Run producers with short-lived identity and minimal access. Keep producer
   artifacts separate from candidate-controlled files. Verify producer identity,
   revision and artifact digest before using evidence at the release boundary.
   [GitHub artifact provenance](https://docs.github.com/en/actions/concepts/workflows-and-actions/workflow-artifacts)
3. Bind delivery to a trusted run and exact release artifact. Make pass, block
   and error behavior visible in the change record. Confirm expected fail-closed
   behavior with missing and mismatched check results.
4. Keep raw findings and logs inside the owning system. Ship only normalized
   decisions to CyberOps and retain them according to the enterprise audit policy.
5. Pilot on one component before expanding. Production readiness still requires
   authenticated artifact verification in the deployment path, organization-wide
   access controls, and evidence retention and support ownership.

Production traces stay outside CyberOps. The current GitHub workflow runs the
native gate and tests, and the exporter is available for a separately configured
producer job.
