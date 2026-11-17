# CyberOps

## About

### Product vision

> This platform orchestrates coordinated red, blue, and purple team swarms to deliver continuous, autonomous cyber operations. By bridging reinforcement learning with real-time threat intelligence, it actively simulates adversary tactics and closes defense gaps offline and inline. It replaces static playbooks with decentralized decision-making that anticipates complex multi-step intrusion chains before they materialize. The system instantly translates discovered exposures into verified remediation paths and self-healing containment rules without human latency. Ultimately, it transforms enterprise security from a reactive burden into an adaptive, closed-loop engine of continuous resilience

### Current implementation

CyberOps orchestrates coordinated Red, Blue, and Purple teams to help enterprises
find security gaps, validate fixes, and learn from recurring failures. It
combines static analysis, revision-bound CI evidence, and offline simulations
with a deterministic release gate. Blue teams receive prioritized remediation
guidance. Purple teams verify fixes and turn approved lessons into regression
requirements. The platform is model-agnostic and keeps production traces
outside the current workflow.

See the [enterprise capability map](docs/enterprise-resilience.md) for the ten
objectives, current capabilities, and roadmap.

| Team | Agents | Handoff |
| --- | --- | --- |
| Red | Supply-chain reviewer and runtime-identity reviewer | Parallel static checks identify unpinned build stages and missing explicit non-root identity in the final stage. |
| Blue | Triage and remediation | Adds risk, severity, ownership and a concrete change for each observation. A component owner applies the change in Git. |
| Purple | Verification and learning | Compares baseline and candidate evidence, makes the gate decision and records lessons for review. |

The article's decision traces, bounded authority, remediation validation and feedback loop map to a reviewable JSON artifact, a fixed set of checks, reruns against the revised build recipe and owner-reviewed lessons. Production telemetry is outside this system's inputs. Learning uses Git baseline files and versioned policy. [Agentic Security Framework](https://medium.com/@bijit211987/agentic-security-framework-1c253af8a223)

## Run it locally

Use Python 3.10 or later with no external packages.

```sh
python3 -m cyberops --root examples/before \
  --inventory examples/components.json --report /tmp/cyberops-before.json

python3 -m cyberops --root examples/after --baseline-root examples/before \
  --inventory examples/components.json --report /tmp/cyberops-after.json
```

The first command exits 1 with two policy findings. The second exits 0 with both rules marked resolved and lessons attached. Exit 2 indicates invalid, missing or unsupported evidence. The example digest is a placeholder for static verification. Use a verified registry digest in deployable images.

A report binds each successful assessment to SHA-256 hashes of the reviewed Dockerfiles. Differences are tracked per component and rule. A rule with one remaining occurrence stays open. Purple confirms that the static policy now passes. Application build and functional checks belong in separate CI jobs.

## Connect a repository

1. Add this project and workflow to the trusted base branch. Change `cyberops-components.json` to list actual service names, owners and repository-relative Dockerfile paths.
2. The pull request workflow reads the registered Dockerfiles as data. The engine and inventory come from the base commit, and the job checks the candidate SHA before assessment. Keep the job free of secrets, write permissions, caches and commands that execute the candidate checkout.
3. Before wiring the gate into a deployment workflow, verify on GitHub that the decision applies to the exact release revision. Require trusted candidate checks and owner review of policy, inventory and workflow changes through repository rules. The supplied workflow does not deploy.
4. Use each uploaded report during remediation review. Promote recurring lessons through reviewed changes to the rules and regression suite.

## Scope and next milestones

The Dockerfile parser supports a limited syntax and returns an error for constructs such as continuation lines, heredocs and custom parser directives. Pin checking validates the reference format, while provenance and image availability require separate evidence. The first release uses static reviews and remediation guidance. It has no model provider, active attack runner, automatic patch writer, production credentials or telemetry connector.

1. Map critical services and their trust boundaries to reviewed ownership and inventory entries.
2. Add defensive scanner adapters for dependency, IaC and secret findings. Require scanner freshness and artifact identity before relying on their results.
3. Validate patches through isolated builds and normal functional tests. Add trusted release-revision attestations and reviewed, expiring policy exceptions.
4. Track open, resolved and recurring findings by component. Turn approved lessons into versioned regression checks and audit evidence.

## Evaluate CI check evidence

A trusted CI producer can normalize defensive check outcomes into JSON with a
full Git commit SHA and a list of component, check and status records. Supported
statuses are `pass`, `fail` and `error`. Keep raw scanner output and logs in the
producer job. Set `required_checks` on each inventory entry to define coverage.
A failed required check blocks, and a missing or errored required check fails
closed. Purple reports a CI rule as resolved only when baseline evidence records
a failure and the candidate records a pass.

```sh
python3 -m cyberops --root examples/after --baseline-root examples/before \
  --inventory examples/evidence/components.json \
  --evidence examples/evidence/after.json \
  --revision 2222222222222222222222222222222222222222 \
  --baseline-evidence examples/evidence/before.json \
  --baseline-revision 1111111111111111111111111111111111111111 \
  --report /tmp/cyberops-evidence.json
```

The files in this example contain synthetic CI results. In a real pipeline, supply
the evidence via an artifact from a trusted producer job and the expected SHA
from trusted CI metadata. A SHA field match and content hash bind the report to
the supplied evidence. The artifact channel must establish producer identity.
The included GitHub workflow continues to use Dockerfile checks until a trusted
producer is connected.

## Reuse skills and carry lessons forward

The CLI uses `cyberops.harness.Harness`. Trusted Python callers can compose their
own harness and pass it to `run(..., harness=...)`. Red reviewers can run with a caller-supplied executor
and return rule and line observations from parsed Dockerfile instructions. Blue
triage and remediation enrich those observations. The CI review skill evaluates
normalized check evidence and returns findings with rule, severity, risk, owner
and remediation. Purple's deterministic verification sets the gate. Its
replaceable learning skill receives copies of the findings and verdict.

An optional `AdvisoryModel` adapter implements `explain(findings)` and receives
only rule IDs and severities. Its text appears in the report as an advisory. The
default harness runs offline without a model. Provider configuration and request
timeouts belong in the adapter.

When Purple verifies a resolved CI finding, its lesson includes a
`suggested_required_check`. A component owner can promote it by adding an entry
such as `{"component": "example-service", "check": "guardrail-regression"}` to the
trusted `cyberops-learning.json` file. Later runs apply that requirement through
`--learning`, even if it is removed from the inventory. GitHub Actions reads
this policy from the trusted checkout. Connect the evidence producer before
promoting checks in the included workflow so CI can supply their results.

## Architecture and metrics

- [Architecture, flowchart and animated walkthrough](docs/architecture.md)
- [Demo results and operational metrics](docs/metrics.md)
- [Agentic platform comparison and roadmap](docs/platform-comparison.md)
- [Enterprise connector catalog and evidence exporter](docs/connectors.md)

## License

Use CyberOps under either the [MIT License](LICENSES/MIT.txt) or
[Apache License 2.0](LICENSES/Apache-2.0.txt).

## Plugin deployment modes

Use the [standalone team plugins or consolidated bundle](docs/plugins.md).
The same guide explains how to use trusted CI history to prioritize recurring findings.

- [Defensive learning benchmark and 20-point swarm roadmap](docs/defensive-learning.md)

## Install and simulate

```sh
python -m pip install -e .
cyberops-simulate --seed 42 --steps 10
docker compose run --rm simulation
```

The simulation emits a JSON audit log and decision counts for synthetic control
reviews. The container has no runtime network access. See the
[swarm architecture and 30-item status](docs/ARCHITECTURE.md) and
[contributor guide](docs/CONTRIBUTING.md). For learning and CI evidence examples,
see the [defensive replay](docs/defensive-learning.md) and
[CI evidence quickstart](#evaluate-ci-check-evidence).

- [Purple review ledger and offline learning feedback](docs/purple-ledger.md)

- [One-page status and signed evidence setup](docs/one-page-status.md)
