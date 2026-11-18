# CyberOps operator console

The console combines a browser UI, a versioned HTTP API, and a service layer
that reads the existing CI report and uses the Purple review ledger. JavaScript
runs in the browser. The server and its packaged frontend assets only require
Python. There is no frontend build step.

| Layer | Responsibility |
| --- | --- |
| Browser | Release decision, evidence coverage, searchable findings, reviewed context, and the review queue. |
| HTTP API | Same-origin requests with named bearer credentials. Viewers can read. Reviewers can also import current findings and label pending cases. |
| Services and storage | Read one operator-configured report, deduplicate findings in SQLite, and bind review writes to the displayed policy. Existing CLI commands can export labels for offline learning. |

## Run the pilot

Install the [0.2.0 wheel](../releases/v0.2.0/cyberops-0.2.0-py3-none-any.whl) or use `python -m pip install -e .`. Create a demo report.
This fixture exits 1 to indicate a blocked candidate.

```sh
cyberops --root examples/before --inventory examples/components.json \
  --candidate-revision 1111111111111111111111111111111111111111 \
  --report /tmp/cyberops-console-report.json
```

Create a random reviewer token in your local shell. Copy the printed token
into the browser when prompted. The server receives and stores only its hash
in the credential configuration.

```sh
eval "$(python - <<'PY'
import hashlib, json, secrets, shlex
token = secrets.token_urlsafe(32)
config = {"analyst": {"role": "reviewer", "sha256": hashlib.sha256(token.encode()).hexdigest()}}
print("export CYBEROPS_CONSOLE_CREDENTIALS=" + shlex.quote(json.dumps(config)))
print("printf '%s\\n' " + shlex.quote(token))
PY
)"
cyberops-console --report /tmp/cyberops-console-report.json --db /tmp/cyberops-console.db
```

Open `http://127.0.0.1:8080`. Connect, search for `IMAGE_PIN`, expand its
remediation guidance, and import current findings into the review queue.
Record a priority or standard label to complete a review. The same import
can be repeated without duplicating cases. For a real pilot, use protected
paths for both the report and SQLite database and publish the report through
a trusted CI artifact handoff.

## API v1

| Method and path | Access | Request and response |
| --- | --- | --- |
| `GET /api/v1/overview` | Viewer or reviewer | Returns the current report, pending cases under its policy, and caller role. |
| `POST /api/v1/import` | Reviewer | Send an empty JSON object to import the configured report. Returns the count of newly inserted cases. |
| `POST /api/v1/reviews` | Reviewer | Send case `id`, `policy` digest and `label` of `standard` or `priority`. Reviewer identity comes from the credential. |

The listener binds to loopback. The browser holds the token in memory and
clears it at disconnect or page reload. This is a single-repository pilot
console. A shared deployment needs enterprise identity, TLS, centralized
audit and retention, a managed service runtime, and tested backup and restore.
Production telemetry and live response remain outside this package.
