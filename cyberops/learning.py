"""Apply approved regression requirements from versioned policy."""

import json

from .evidence import IDENTIFIER, REVISION

MAX_HISTORY_BYTES = 1_000_000


def apply_learning(components, path):
    policy = json.loads(path.read_text())
    if not isinstance(policy, list):
        raise ValueError("Learning policy must be a list of approved regression requirements")
    approved = {component["name"]: set() for component in components}
    for entry in policy:
        if not isinstance(entry, dict) or set(entry) != {"component", "check"}:
            raise ValueError("Learning policy entries require a component and check")
        component, check = entry["component"], entry["check"]
        if not isinstance(component, str) or component not in approved:
            raise ValueError("Learning policy references an unknown component")
        if not isinstance(check, str) or not IDENTIFIER.fullmatch(check):
            raise ValueError("Learning policy contains an invalid check")
        if check in approved[component]:
            raise ValueError("Learning policy contains a duplicate requirement")
        approved[component].add(check)

    return [
        {**component, "required_checks": sorted(set(component.get("required_checks", [])) | additions)}
        if (additions := approved[component["name"]]) else component
        for component in components
    ]


def identify_recurring_findings(report, paths):
    """Use bounded, same-policy historical reports as advisory feedback."""
    resolved = set()
    used_revisions = set()
    policy = report["effective_policy_sha256"]
    for path in paths:
        try:
            with path.open("rb") as stream:
                data = stream.read(MAX_HISTORY_BYTES + 1)
            if len(data) > MAX_HISTORY_BYTES:
                raise ValueError("History report exceeds size limit")
            previous = json.loads(data)
            if not isinstance(previous, dict) or previous.get("schema_version") != 1:
                raise ValueError("Unsupported history report")
            revision = previous.get("candidate_revision")
            if (previous.get("effective_policy_sha256") != policy
                    or not isinstance(revision, str) or not REVISION.fullmatch(revision)
                    or revision == report.get("candidate_revision")):
                continue
            prior_resolutions = {
                (item["name"], rule) for item in previous["components"]
                if item["purple"]["decision"] in ("pass", "block")
                for rule in item["purple"]["resolved_rules"]
                if isinstance(rule, str)
            }
        except (OSError, ValueError, TypeError, KeyError, RecursionError):
            continue
        resolved.update(prior_resolutions)
        used_revisions.add(revision)

    recurring = sorted({
        (item["name"], finding["rule"])
        for item in report["components"] for finding in item.get("findings", [])
        if (item["name"], finding["rule"]) in resolved
    })
    return {
        "historical_revisions": len(used_revisions),
        "history_inputs": len(paths),
        "recurring_findings": [
            {"component": component, "rule": rule, "action": "prioritize regression review"}
            for component, rule in recurring
        ],
    }
