"""Validate normalized defensive check results from a trusted CI producer."""

import hashlib
import json
import re
from pathlib import Path

IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}")
REVISION = re.compile(r"[0-9a-f]{40}")
MAX_EVIDENCE_BYTES = 1_000_000


def load_evidence(path, revision):
    if not REVISION.fullmatch(revision):
        raise ValueError("Expected a full Git commit SHA for CI evidence")
    with Path(path).open("rb") as source:
        data = source.read(MAX_EVIDENCE_BYTES + 1)
    if len(data) > MAX_EVIDENCE_BYTES:
        raise ValueError("CI evidence is oversized")
    try:
        report = json.loads(data)
    except (UnicodeError, json.JSONDecodeError):
        raise ValueError("Invalid CI evidence JSON") from None
    if (
        not isinstance(report, dict)
        or set(report) != {"schema_version", "revision", "checks"}
        or type(report["schema_version"]) is not int
        or report["schema_version"] != 1
        or report["revision"] != revision
        or not isinstance(report["checks"], list)
    ):
        raise ValueError("CI evidence has an invalid schema or revision")
    checks = {}
    for check in report["checks"]:
        if not isinstance(check, dict) or set(check) != {"component", "check", "status"}:
            raise ValueError("Invalid CI evidence check")
        component, name, status = check["component"], check["check"], check["status"]
        if any(not isinstance(value, str) or not IDENTIFIER.fullmatch(value)
               for value in (component, name)):
            raise ValueError("Invalid CI check identifier")
        if status not in ("pass", "fail", "error") or (component, name) in checks:
            raise ValueError("Invalid or duplicate CI check status")
        checks[component, name] = status
    return checks, {"revision": revision, "sha256": hashlib.sha256(data).hexdigest()}


def review_checks(component, checks):
    """Red checks the coverage recorded by CI. Blue attaches remediation."""
    findings = []
    for check in component.get("required_checks", []):
        status = checks.get((component["name"], check))
        if status not in ("pass", "fail"):
            raise ValueError(f"Required CI check {check} is missing or errored")
        if status == "fail":
            findings.append({
                "rule": f"CI.{check}",
                "severity": "high",
                "risk": "A required defensive CI check failed.",
                "owner": component["owner"],
                "remediation": f"Review the {check} job, correct the failed control, and rerun it.",
            })
    return findings
