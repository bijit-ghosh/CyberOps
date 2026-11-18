# CyberOps 0.1.0

Initial release package for a controlled CI pilot. This release includes the
offline gate, standalone Red, Blue, and Purple plugins, signed CI evidence
verification, and the Purple review and feedback tools.

## Install and run

Download the [Python wheel](cyberops-0.1.0-py3-none-any.whl) and
[SHA-256 checksum](SHA256SUMS). Use a Python 3.12 virtual environment for the
same runtime family used in local release validation.

```sh
sha256sum -c SHA256SUMS
python3.12 -m venv .venv
.venv/bin/python -m pip install --no-deps cyberops-0.1.0-py3-none-any.whl
.venv/bin/cyberops-simulate --seed 42 --steps 10
```

On Windows, use the corresponding executables under `.venv\Scripts`.
The checksum identifies the wheel bytes. Authenticate the source of the
checksum before using it as a supply-chain control.

## Choose a deployment model

| Choice | Why use it | Trade-off |
| --- | --- | --- |
| Python 3.12 with the wheel | Reproduces the tested release environment. The wheel installs without third-party runtime packages. | Your team owns runtime patching and runner lifecycle. |
| Python 3.10 with the wheel | Maintains compatibility with existing CI runners. It is the declared minimum. | This release was validated locally on 3.12. Verify the 3.10 CI matrix before relying on it. |
| Managed CI runner | Providers provision Python and retain workflow artifacts. Developers can consume the gate through the CLI and JSON. | You still need trusted producer jobs, repository rules, and verification against the exact release SHA. |
| Container | Standardizes the runtime without requiring Python on every host. | Requires a container engine, a reviewed base-image digest, and a deployment test. The supplied Compose setup runs the offline simulation. |
| External integration in Node.js, Go, or another stack | Keeps enterprise tooling in its existing language using the JSON contracts and exit codes. | The reference gate still needs Python on its execution runner. See [interoperability](../../docs/interoperability.md). |

Signed CI evidence additionally requires OpenSSL 3 and a trusted producer key.
Enterprise readiness also depends on identity and key rotation, artifact
freshness, exact-revision enforcement, retention, and recovery ownership.

## Ten release checks

| Check | Result |
| --- | --- |
| Wheel build and checksum | Passed |
| Clean install outside the source checkout and dependency consistency | Passed |
| All six installed CLI entry points | Passed |
| Full test suite against the installed wheel | Passed, 20 tests |
| Signed evidence and tamper rejection | Passed in the installed-wheel suite |
| Node.js report consumption and revision mismatch rejection | Passed |
| Compose configuration | Passed |
| Hosted CI matrix, including Python 3.10 | Pending remote verification |
| Container build and execution | Pending. The local Docker daemon denied access. |
| Real enterprise pilot with an authenticated producer and exact-SHA enforcement | Pending deployment validation |

Seven checks passed locally and three remain open. The release is suitable for
a controlled pilot. Production sign-off requires evidence from the deployment
environment, including recovery and key-rotation exercises.
