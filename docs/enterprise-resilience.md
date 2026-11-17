# Enterprise resilience

CyberOps gives teams a reviewable path from CI evidence to remediation,
verification and regression policy. It keeps provider choice open and uses
deterministic controls for release decisions.

## Enterprise pressures

| Challenge | CyberOps response today |
| --- | --- |
| Short remediation windows | Evaluate candidates in CI and give owners a ranked remediation queue. Track time to verified fix using retained reports. |
| Compound exposure | Accept candidate-bound reachability context from an approved producer. Preserve unknowns and keep each finding visible. |
| AI-service risk | Require pre-authored defensive guardrail results from trusted CI jobs, including authorization and data-boundary checks. |
| Triage friction | Blue assigns findings and guidance. Purple verifies revision evidence, flags recurrence and records review labels for offline evaluation. |

## Ten objectives

| # | Objective | Current implementation or roadmap |
| --- | --- | --- |
| 1 | Adversarial exposure validation | Static control review and synthetic defensive scenarios. Reviewed assessment outcomes may enter CI as evidence. |
| 2 | Remediation discovery and validation | Blue recommends changes. Purple compares a revised candidate with its baseline. Build, test and apply changes through the owning pipeline. |
| 3 | AI guardrails | Register required defensive guardrail checks and ingest normalized outcomes. Runtime interception is outside the current deployment. |
| 4 | Closed-loop defense | Replay reviewed CI cases offline and promote approved regression requirements through Git. Release decisions stay deterministic. |
| 5 | Context-rich prioritization | Optional reachability context joins findings by component and rule, with explicit unknowns and a revision check. A trusted upstream producer supplies the reachability conclusion. |
| 6 | Shared Purple intelligence | The local review ledger deduplicates findings and exports reviewed labels. Policy change remains owner-reviewed. |
| 7 | Containment readiness | Future defensive response integrations need authenticated approvals, protected-asset controls and rollback. |
| 8 | Resilience to changed inputs | Offline fixtures test unknown-control fallback. Extend coverage with reviewed benign boundary cases. |
| 9 | Explainable attribution | Per-component decision traces and queue fields expose control, owner, severity and reachability. Cross-component incident graphing remains future work. |
| 10 | Zero trust and oversight | Trusted checkout, revision matching and analyst review are available. Producer authentication, distributed identity and authenticated approvals remain deployment work. |

## Try the exposure queue

```sh
python -m cyberops --root examples/before \
  --inventory examples/components.json \
  --candidate-revision 1111111111111111111111111111111111111111 \
  --exposure-context examples/exposure-context/reachability.json \
  --report /tmp/cyberops-exposure.json
```

The demo blocks with two findings. The queue sorts severity first and uses
reachability to break ties, ahead of component and rule identifiers. Findings
are grouped by component and rule for triage, while the gate report preserves
individual observations. Missing context stays unknown. Invalid or stale
context produces an advisory error and a severity-only queue. Neither outcome
changes the release decision. The example uses synthetic reachability.

Use an authenticated artifact channel to establish the context producer's
identity. The revision field and SHA-256 identify the expected revision and
the input bytes. They do not verify the reachability claim independently.
