# CyberOps · One-page status

CyberOps is a model-agnostic CI security gate with standalone Red, Blue and
Purple plugins and a bundled CLI. It reviews build controls, prioritizes
findings, verifies revised evidence and feeds analyst-reviewed cases into
offline evaluation. GitHub's README carries the full product vision alongside
the current implementation.

## Delivered in this update

**Signed CI evidence.** A trusted CI producer can sign normalized evidence with
an Ed25519 key. The gate verifies the detached signature against a pinned
public key before parsing the exact verified bytes. The expected revision
must still match, and signed mode requires signatures for any baseline
evidence included in the evaluation. Missing or invalid signatures fail closed.
The default local demo continues to accept unsigned fixture evidence.

```sh
# Trusted producer. Keep the private key outside the checkout.
openssl pkeyutl -sign -inkey producer-private.pem -rawin \
  -in evidence.json -out evidence.sig
# Trusted consumer. Obtain the expected SHA and public key independently.
python -m cyberops --root candidate --inventory trusted/components.json \
  --revision "$EXPECTED_SHA" --evidence evidence.json \
  --evidence-public-key trusted/producer-public.pem \
  --evidence-signature evidence.sig --report report.json
```

Use OpenSSL 3 and an Ed25519 key pair. Store or provision the pinned public key
outside candidate control. This verifies producer key possession and artifact
integrity. Deployment owners still need key rotation and source artifact
freshness or run binding. The existing GitHub workflow needs an actual producer
before signature mode can be enforced remotely.

## Verification and remaining scope

Seventeen local tests passed, including signature verification, tampered-byte
rejection and wrong-revision rejection. The remote evidence producer and Actions
execution are unverified. Distributed identity and RBAC, authenticated
approvals, worker supervision, external messaging, shared knowledge graph,
OpenTelemetry, dashboards, native integrations and defensive model promotion
remain unimplemented. Production telemetry remains disconnected. Autonomous
intrusion, exploit mutation, stealth optimization and live offensive policy
transfer are outside CyberOps' implementation.

## Readiness audit · 2026-11-18

**Disposition: ready for a controlled CI pilot.** Production readiness remains
unverified. The pilot scope is the offline release gate and sample defensive
workflows.

| Area | Result |
| --- | --- |
| Repository structure | Explicit Python packages, separate team plugins, docs, examples and tests. Renamed a case-only documentation path collision for case-insensitive filesystems. Docker build context is restricted to application source. |
| Functional validation | 18 tests passed on Python 3.12. This includes signed evidence, connector-to-gate behavior, replay, learning, and replacement of stale reports after invalid input. |
| Distribution | Built and installed the wheel in a clean virtual environment. All five installed commands responded outside the checkout, and the simulation emitted 30 events across ten steps. |
| CI | Added a Python 3.10/3.12 matrix and installed-wheel smoke test. The hosted matrix and GitHub release gate still need a verified run. |
| Docker | Compose config validates. Building and running the container remain unverified because the local Docker daemon is inaccessible. |

For a production decision, run the gate on a real protected repository with a
trusted signed evidence producer, confirm the required check applies to the
exact release SHA, and exercise failure recovery and key rotation. Establish
evidence retention, access controls and support ownership in that environment.
Distributed runtime operation and its associated controls remain outside the
verified pilot scope.
