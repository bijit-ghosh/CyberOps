# Standalone and bundled plugins

Use the standalone Python interfaces to place team handoffs in separate enterprise
jobs or services. Each interface works offline and has no model dependency.

```python
from cyberops.plugins import blue, purple, red

observations = red.review(dockerfile_bytes)
findings = blue.remediate(component, observations)
findings.extend(red.review_checks(component, trusted_check_results))
result = purple.verify(findings, previous_rule_ids)
```

The Red interface statically reviews build controls and ingests completed
defensive check results. Blue provides triage and remediation guidance. Purple
produces the gate result and regression proposals. An enterprise owns the trust
boundary and transport between standalone jobs.

For an integrated deployment, use the existing `python3 -m cyberops` CLI and
GitHub workflow or import `CyberOps` from `cyberops.plugins.bundle`. Both paths use
the same plugin code. The CLI runs the two small static rules inline to avoid
thread startup and scheduling. An embedding application can supply its own
executor for heavier independent reviewers. Python's standard library is the
only runtime dependency.

## Continuous learning from CI history

Supply archived trusted decision reports as repeatable `--history PATH` arguments.
Retain the exact candidate revision by passing `--candidate-revision SHA` when
producing those reports. Use reports from earlier runs of the same component
policy. The CLI accepts up to 20 inputs and reads at most 1 MB per history report.

CyberOps flags an open component-rule pair when a comparable earlier revision
recorded that rule as resolved. The report counts distinct usable historical
revisions and lists recurring findings for regression review. Malformed reports
and different-policy reports are skipped. History provides advisory feedback.
Owners approve new required checks in the versioned learning policy, and Purple
continues to make its decision from the current evidence. No runtime traces
or model training are needed.
