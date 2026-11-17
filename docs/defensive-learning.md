# Defensive learning and swarm roadmap

CyberOps keeps standalone Red, Blue and Purple plugins and the consolidated
CI gate. This release adds a separate offline benchmark for advisory Blue
review routing. Purple's release decision continues to use configured policy.
Production telemetry remains disconnected.

## Run the benchmark

```sh
python3 -m cyberops.envs.replay \
  --training examples/defensive-replay/training.json \
  --held-out examples/defensive-replay/held-out.json
```

Each case has an ID, a control and a reviewed queue label. The learner
calculates support by control using reviewed training cases. A recommendation
requires at least three observations and 80% agreement. Unknown or uncertain
cases return to manual review. The evaluator compares recommendations with
disjoint held-out case IDs and reports the rationale, evidence counts, input
digests, coverage, fallbacks and missed-priority cases. Re-run with new reviewed
labels as more data becomes available. Promote policy changes through Git review.

The synthetic demo produced one correct recommendation and two manual-review
fallbacks across three cases. This is a fixture check. For enterprise
evaluation, deduplicate related cases before splitting and use a chronological
holdout, authenticated reviewers and versioned datasets. Digests identify
inputs and do not establish who approved the labels.

## Disposition of the 20 proposals

| # | Proposal | CyberOps disposition |
| --- | --- | --- |
| 1 | MARL / CTDE | Offline supervised review routing is implemented. Future multi-agent evaluation can use bounded defensive decisions and explicit per-role visibility. |
| 2 | Offline-to-inline transfer | Offline evaluation and advisory review. The live release gate stays deterministic. |
| 3 | Swarm task allocation | Independent plugins are available. A future coordinator can allocate static reviews, validation and evidence triage. |
| 4 | Purple feedback | Existing CI recurrence feedback and owner-approved regression policy. The new benchmark measures routing against reviewed labels. |
| 5 | C2 orchestration | Use reviewed defensive assessment outcomes as evidence. |
| 6 | Blue self-healing | Existing remediation guidance and CI verification. Future defensive actions need scoped permissions, approval and rollback. |
| 7 | Reward shaping | Evaluate defensive prioritization by missed priorities, recommendation accuracy and manual-review load. |
| 8 | ATT&CK and D3FEND | Future read-only taxonomy references for control coverage and validated detections. |
| 9 | Offline replay | Bounded labeled JSON datasets and separate held-out evaluation are implemented. |
| 10 | Zero trust | Distributed deployment still needs workload identity, mTLS and signed, expiry-bound evidence with replay protection. |
| 11 | Digital twin | Synthetic control cases are available. Future defensive simulation can use sanitized declarative topology and mock assets. |
| 12 | Explainability | Per-case support and fallback rationale are implemented. |
| 13 | Hierarchical swarms | The bundle coordinates standalone plugins. Role-specific worker scheduling remains future work. |
| 14 | Playbooks and auditing | Current decision traces and regression proposals are available. Future exports can be reviewed before promotion. |
| 15 | OOD guardrails | Unseen controls and insufficient support trigger manual review. Statistical drift monitoring remains future work. |
| 16 | Circuit breakers | Dataset size is bounded and the evaluator has no action executor. Distributed worker budgets and pause controls remain future work. |
| 17 | Federated learning | Future research can aggregate defensive statistics across approved boundaries after privacy and integrity testing. |
| 18 | Poisoning defense | Strict input shape, unique IDs, a split-overlap check and input digests are implemented. Dataset authenticity and reviewer independence still need controls. |
| 19 | Telemetry streaming | Current scope uses CI artifacts. Future streaming work can consume allowlisted defensive summaries with backpressure and measured latency. |
| 20 | Analyst override | Manual review fallback is implemented. An authenticated analyst console and recorded overrides remain future work. |

The benchmark lives under `cyberops/envs/` and the three team interfaces remain
under `cyberops/plugins/`. Separate learning and swarm packages can be introduced
when multiple learners or distributed coordinators need shared interfaces.
