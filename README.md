# CyberOps

## About

CyberOps is designed as a coordinated multi-agent swarm to continuously simulate advanced adversary tactics (Red), detect and isolate emerging threats in real time (Blue), and dynamically improve security posture through shared intelligence (Purple). Today, CyberOps brings that operating model to pre-release CI/CD and offline defensive evaluation.

## Mission

Help every organization build and operate software and AI systems that get harder to compromise with every release. Make security a continuous engineering practice, where teams can act at machine speed, prove that their controls work, and remain accountable for decisions that affect critical services.

## Product vision

CyberOps will connect preventive testing, detection, response, and learning across the software lifecycle. Red will use authorized, controlled simulations to challenge assumptions about how applications and AI services are protected. Blue will turn trusted signals into prioritized decisions and contain threats within approved limits. Purple will verify that fixes work and turn lessons across teams into stronger controls and regression tests.

Teams will be able to adopt those capabilities independently or as a coordinated swarm, choose their models and tools, and decide where automation can act. Every consequential decision should be traceable to evidence, an owner, and an approval policy.

## What we’ve achieved

| Team | Shipped capabilities |
| --- | --- |
| Red | Reviews container build controls and evaluates defensive check results supplied by CI. |
| Blue | Gives findings an owner, severity, and next step. The CI summary can surface reviewed reachability, control, identity, and data context. |
| Purple | Makes a deterministic release decision, verifies fixes against a baseline, and proposes regression checks. The review ledger feeds analyst-labeled cases into offline evaluation. |

CyberOps provides standalone team plugins and a bundled, model-agnostic CLI. It supports revision-bound evidence, optional signature verification, and stable finding IDs across open and resolved CI summaries. The current workflow uses pre-release evidence and keeps production traces disconnected. [Architecture](docs/architecture.md) · [Readiness and verification](docs/one-page-status.md)

## What we need to achieve

1. **Prove the full loop on mission-critical services.** Connect authenticated evidence producers, require the gate on the exact release revision, and verify real application and AI guardrail fixes in their normal pull-request workflows.
2. **Make risks explainable across the enterprise.** Connect services, dependencies, identities, controls, data classes, and ownership so teams can see what is affected and what evidence supports the decision.
3. **Move from recommendations to governed response.** Establish authenticated approvals, scoped actions, protected-service safeguards, and rollback. Validate response policies offline before introducing authorized live detection and containment.
4. **Turn each verified fix into durable protection.** Carry approved lessons across components, validate changes against held-out evidence, and measure time to verified fix, recurrence, and control coverage.
5. **Scale with deployment flexibility.** Support enterprise CI and security integrations, independently deployable teams, and traceable decisions across environments and model providers.

[Enterprise capability map and examples](docs/enterprise-resilience.md) · [Founding design article](https://medium.com/@bijit211987/agentic-security-framework-1c253af8a223)

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

## Documentation

Use the [documentation index](docs/README.md) to find operator quickstarts,
integration contracts, architecture and readiness status.

## License

CyberOps is licensed under [Apache License 2.0](LICENSE).

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
[swarm architecture and 30-item status](docs/swarm-architecture.md) and
[contributor guide](docs/CONTRIBUTING.md). For learning and CI evidence examples,
see the [defensive replay](docs/defensive-learning.md) and
[CI evidence quickstart](#evaluate-ci-check-evidence).

