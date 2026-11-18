"""Render a CyberOps decision report for a GitHub Actions job summary."""

import argparse
import json
import string
from hashlib import sha256
from pathlib import Path

from .prioritization import prioritize

MAX_ENTRIES = 25
ESCAPES = str.maketrans({character: f"&#{ord(character)};" for character in string.punctuation})


def plain(value):
    # Render data as text even when it resembles Markdown or HTML.
    return " ".join(str(value).split())[:400].translate(ESCAPES)


def finding_id(component, rule):
    key = json.dumps([component, rule], separators=(",", ":")).encode("utf-8")
    return "CO-" + sha256(key).hexdigest()[:16]


def render(report):
    if report.get("schema_version") != 1 or report.get("decision") not in ("pass", "block", "error"):
        raise ValueError("Unsupported CyberOps decision report")
    lines = [f"## CyberOps · {report['decision'].upper()}", ""]
    revision = report.get("candidate_revision") or report.get("ci_evidence", {}).get("revision")
    if revision:
        lines.extend([f"**Candidate revision** {plain(revision)}", ""])
    if "error" in report:
        lines.extend([f"**Assessment error** {plain(report['error'])}", ""])

    components = {item["name"]: item for item in report.get("components", [])}
    for item in list(components.values())[:MAX_ENTRIES]:
        if "error" in item:
            lines.extend([f"**Assessment error for {plain(item['name'])}** {plain(item['error'])}", ""])

    triage = report.get("triage", {})
    if triage.get("status") == "error":
        lines.extend(["Reachability and reviewed context could not be loaded. See the JSON report.", ""])
    queue = triage.get("queue")
    if queue is None:
        queue = prioritize({"components": components.values()}, {})
    if queue:
        lines.extend(["### Open findings", ""])
    for row in queue[:MAX_ENTRIES]:
        component, rule = row["component"], row["rule"]
        observation = next(
            f for f in components[component]["findings"]
            if f["rule"] == rule and f["severity"] == row["severity"]
        )
        lines.extend([
            f"#### {finding_id(component, rule)} · {plain(rule)}",
            "",
            f"- **Component** {plain(component)} · **Owner** {plain(row['owner'])} "
            f"· **Severity** {plain(row['severity'])}",
            f"- **Risk** {plain(observation['risk'])}",
            f"- **Next step** {plain(observation['remediation'])}",
            f"- **Reachability** {plain(row['reachability'])}",
        ])
        for link in row.get("relationships", []):
            lines.append(f"- **Reviewed context** {plain(link['relationship'])} · {plain(link['target'])}")
        lines.append("")
    if len(queue) > MAX_ENTRIES:
        lines.extend([f"{len(queue) - MAX_ENTRIES} more open findings are in the JSON report.", ""])

    resolved = [
        (item, rule) for item in components.values()
        for rule in item["purple"].get("resolved_rules", [])
    ]
    if resolved:
        lines.extend(["### Verified against the baseline", ""])
    for item, rule in resolved[:MAX_ENTRIES]:
        lines.append(f"- **{finding_id(item['name'], rule)}** · {plain(item['name'])} · {plain(rule)}")
        for lesson in item.get("lessons", []):
            if lesson["rule"] == rule and lesson.get("suggested_required_check"):
                lines.append(f"  - **Regression proposal** {plain(lesson['suggested_required_check'])}")
    if len(resolved) > MAX_ENTRIES:
        lines.append(f"- {len(resolved) - MAX_ENTRIES} more resolved rules are in the JSON report.")
    lines.extend(["", "See the `cyberops-report` artifact for the complete evidence and decision trace."])
    return "\n".join(lines).rstrip() + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    try:
        print(render(json.loads(args.report.read_text(encoding="utf-8"))), end="")
    except (OSError, ValueError, KeyError, TypeError, AttributeError, RecursionError, StopIteration) as error:
        parser.exit(2, f"Cannot render CyberOps summary: {error}\n")


if __name__ == "__main__":
    main()
