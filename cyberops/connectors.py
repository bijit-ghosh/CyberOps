"""Normalize completed defensive checks into CyberOps evidence."""

import argparse
import json
import sys
from pathlib import Path
from xml.etree import ElementTree

from .evidence import IDENTIFIER, MAX_EVIDENCE_BYTES, REVISION


def junit_status(path):
    with path.open("rb") as source:
        data = source.read(MAX_EVIDENCE_BYTES + 1)
    if len(data) > MAX_EVIDENCE_BYTES:
        raise ValueError("JUnit report is oversized")
    text = data.decode("utf-8-sig")
    if "\x00" in text or "<!DOCTYPE" in text or "<!ENTITY" in text:
        raise ValueError("Unsupported JUnit XML declaration")
    root = ElementTree.fromstring(text)
    if root.tag not in ("testsuite", "testsuites"):
        raise ValueError("Expected a JUnit testsuite or testsuites document")
    cases = root.findall(".//testcase")
    if not cases:
        raise ValueError("JUnit report has no tests")
    if any(case.find("error") is not None for case in cases):
        return "error"
    if any(case.find("failure") is not None for case in cases):
        return "fail"
    if any(case.find("skipped") is not None for case in cases):
        return "error"
    return "pass"


def export_evidence(revision, component, checks, junit_reports):
    if not REVISION.fullmatch(revision) or not IDENTIFIER.fullmatch(component):
        raise ValueError("Expected a full Git commit SHA and a valid component identifier")
    results = {}
    for inputs, connector in ((checks, str), (junit_reports, lambda value: junit_status(Path(value)))):
        for name, value in inputs:
            if not IDENTIFIER.fullmatch(name) or name in results:
                raise ValueError("Check identifiers must be valid and unique")
            status = connector(value)
            if status not in ("pass", "fail", "error"):
                raise ValueError("Check status must be pass, fail or error")
            results[name] = status
    if not results:
        raise ValueError("At least one completed check is required")
    return {
        "schema_version": 1,
        "revision": revision,
        "checks": [
            {"component": component, "check": name, "status": status}
            for name, status in sorted(results.items())
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--component", required=True)
    parser.add_argument("--status", nargs=2, action="append", default=[], metavar=("CHECK", "STATUS"))
    parser.add_argument("--junit", nargs=2, action="append", default=[], metavar=("CHECK", "REPORT"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = export_evidence(args.revision, args.component, args.status, args.junit)
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(report, indent=2) + "\n")
    except (OSError, ValueError, ElementTree.ParseError) as error:
        parser.exit(2, f"CyberOps connector error: {error}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
