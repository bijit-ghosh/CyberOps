"""Offline CI security review for registered mission-critical components."""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath

from .evidence import IDENTIFIER, REVISION, load_evidence
from .learning import apply_learning, identify_recurring_findings
from .plugins.bundle import CyberOps

VERSION = 1
MAX_FILE_BYTES = 256_000


def read_file(root, relative):
    path = root / relative
    if not path.resolve().is_relative_to(root) or any(
        parent.is_symlink() for parent in (path, *path.parents) if parent != root
        and parent.is_relative_to(root)
    ):
        raise ValueError(f"Unexpected path for {relative}")
    if not path.is_file() or path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError(f"Missing or oversized file: {relative}")
    return path.read_bytes()


def inventory(path):
    entries = json.loads(path.read_text())
    if not isinstance(entries, list) or not entries:
        raise ValueError("Inventory must contain at least one component")
    seen = set()
    for entry in entries:
        required = {"name", "owner", "dockerfile"}
        if not isinstance(entry, dict) or not required <= set(entry) <= required | {"required_checks"}:
            raise ValueError("Each component requires name, owner and dockerfile")
        if any(not isinstance(v, str) or not v.strip() for v in (entry[key] for key in required)):
            raise ValueError("Component fields must be nonempty strings")
        name, filename = entry["name"], entry["dockerfile"]
        if not re.fullmatch(r"[a-zA-Z0-9_-]+", name) or name in seen:
            raise ValueError("Component names must be unique identifiers")
        path = PurePosixPath(filename)
        if path.is_absolute() or ".." in path.parts or str(path) != filename:
            raise ValueError("Dockerfile must be a normalized repository-relative path")
        checks = entry.get("required_checks", [])
        if (not isinstance(checks, list)
                or any(not isinstance(check, str) or not IDENTIFIER.fullmatch(check) for check in checks)
                or len(set(checks)) != len(checks)):
            raise ValueError("Required CI checks must be unique identifiers")
        seen.add(name)
    return entries


def inspect(root, component, harness, checks):
    data = read_file(root, component["dockerfile"])
    return hashlib.sha256(data).hexdigest(), harness.assess(data, component, checks)


def run(root, components, baseline, checks, baseline_checks, harness=None):
    harness = harness or CyberOps()
    policy = json.dumps(components, sort_keys=True, separators=(",", ":")).encode()
    results = []
    for component in components:
        trace = []
        stage = "baseline"
        try:
            prior = set()
            prior_digest = None
            if baseline is not None and (baseline / component["dockerfile"]).exists():
                prior_digest, previous = inspect(baseline, component, harness, None)
                prior = {finding["rule"] for finding in previous}
            if baseline_checks is not None:
                prior.update(finding["rule"] for finding in harness.review_ci(component, baseline_checks))
            stage = "red_blue_assessment"
            digest, findings = inspect(root, component, harness, checks)
            trace.append({"stage": stage, "status": "complete", "findings": len(findings)})
            stage = "purple_verification"
            purple = harness.evaluate(findings, prior)
            trace.append({"stage": stage, "status": purple["purple"]["decision"]})
            trace.append({"stage": "purple_learning", "status": "complete",
                          "proposals": sum("suggested_required_check" in lesson
                                           for lesson in purple["lessons"])})
            results.append({
                **component, "sha256": digest, "baseline_sha256": prior_digest,
                "findings": findings, "decision_trace": trace, **purple,
            })
        except (OSError, ValueError) as error:
            trace.append({"stage": stage, "status": "error"})
            results.append({**component, "purple": {"decision": "error"},
                            "decision_trace": trace, "error": str(error)})
    decisions = {item["purple"]["decision"] for item in results}
    decision = "error" if "error" in decisions else "block" if "block" in decisions else "pass"
    return {
        "schema_version": VERSION, "decision": decision,
        "effective_policy_sha256": hashlib.sha256(policy).hexdigest(),
        "metrics": {
            "components": {status: sum(item["purple"]["decision"] == status for item in results)
                           for status in ("pass", "block", "error")},
            "required_check_results": {
                status: sum(
                    checks.get((component["name"], check), "missing") == status
                    for component in components for check in component.get("required_checks", [])
                )
                for status in ("pass", "fail", "error", "missing")
            },
        },
        "components": results,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--baseline-root", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--revision")
    parser.add_argument("--candidate-revision", help="Commit SHA from the trusted CI checkout")
    parser.add_argument("--baseline-evidence", type=Path)
    parser.add_argument("--baseline-revision")
    parser.add_argument("--learning", type=Path)
    parser.add_argument("--history", type=Path, action="append", default=[],
                        help="Trusted earlier decision report for advisory learning (up to 20)")
    args = parser.parse_args()
    if len(args.history) > 20:
        parser.error("Provide at most 20 history reports")
    try:
        root = args.root.resolve(strict=True)
        baseline = args.baseline_root.resolve(strict=True) if args.baseline_root else None
        if not root.is_dir() or (baseline is not None and not baseline.is_dir()):
            raise ValueError("Candidate and baseline roots must be directories")
        if args.candidate_revision and not REVISION.fullmatch(args.candidate_revision):
            raise ValueError("Expected a full Git commit SHA for the candidate")
        if args.candidate_revision and args.revision and args.candidate_revision != args.revision:
            raise ValueError("Candidate and CI evidence revisions differ")
        if bool(args.evidence) != bool(args.revision) or bool(args.baseline_evidence) != bool(args.baseline_revision):
            raise ValueError("Each CI evidence file requires its expected revision")
        if args.baseline_evidence and (not baseline or not args.evidence):
            raise ValueError("Baseline CI evidence requires a baseline root and candidate CI evidence")
        checks, evidence = load_evidence(args.evidence, args.revision) if args.evidence else ({}, None)
        previous, baseline_evidence = (
            load_evidence(args.baseline_evidence, args.baseline_revision)
            if args.baseline_evidence else (None, None)
        )
        components = inventory(args.inventory)
        if args.learning:
            components = apply_learning(components, args.learning)
        report = run(root, components, baseline, checks, previous)
        if args.candidate_revision:
            report["candidate_revision"] = args.candidate_revision
        if args.history:
            report["learning_feedback"] = identify_recurring_findings(report, args.history)
        if evidence:
            report["ci_evidence"] = evidence
        if baseline_evidence:
            report["baseline_ci_evidence"] = baseline_evidence
    except (OSError, ValueError) as error:
        report = {"schema_version": VERSION, "decision": "error", "error": str(error)}
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(f"CyberOps decision: {report['decision']}")
    return {"pass": 0, "block": 1, "error": 2}[report["decision"]]


if __name__ == "__main__":
    sys.exit(main())
