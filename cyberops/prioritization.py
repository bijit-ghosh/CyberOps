"""Rank defensive findings using optional revision-bound reachability evidence."""

import json
from hashlib import sha256

from .evidence import IDENTIFIER, MAX_EVIDENCE_BYTES, REVISION

REACHABILITY = {"reachable": 2, "unknown": 1, "unreachable": 0}
SEVERITY = {"critical": 4, "high": 3, "medium": 2, "low": 1}
RELATIONSHIPS = {"validates-control", "uses-identity", "protects-data-class"}
MAX_RELATIONSHIPS = 16


def read_relationships(rows):
    if not isinstance(rows, list) or len(rows) > MAX_RELATIONSHIPS:
        raise ValueError("Exposure relationships must be a bounded list")
    links = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"relationship", "target"}:
            raise ValueError("Invalid exposure relationship record")
        relationship, target = row["relationship"], row["target"]
        if (not isinstance(relationship, str) or relationship not in RELATIONSHIPS
                or not isinstance(target, str) or not IDENTIFIER.fullmatch(target)
                or (relationship, target) in links):
            raise ValueError("Invalid or duplicate exposure relationship")
        links.add((relationship, target))
    return [{"relationship": relationship, "target": target}
            for relationship, target in sorted(links)]


def load_context(path, revision):
    with path.open("rb") as stream:
        data = stream.read(MAX_EVIDENCE_BYTES + 1)
    if len(data) > MAX_EVIDENCE_BYTES:
        raise ValueError("Exposure context exceeds size limit")
    document = json.loads(data)
    if (not isinstance(document, dict) or set(document) != {"schema_version", "revision", "findings"}
            or type(document["schema_version"]) is not int or document["schema_version"] != 1
            or not revision or not REVISION.fullmatch(revision)
            or document["revision"] != revision or not isinstance(document["findings"], list)):
        raise ValueError("Exposure context schema or revision does not match")
    context = {}
    for row in document["findings"]:
        required = {"component", "rule", "reachability"}
        if not isinstance(row, dict) or not required <= set(row) <= required | {"relationships"}:
            raise ValueError("Invalid exposure context record")
        component, rule, state = row["component"], row["rule"], row["reachability"]
        if (any(not isinstance(value, str) or not IDENTIFIER.fullmatch(value)
                for value in (component, rule))
                or not isinstance(state, str) or state not in REACHABILITY or (component, rule) in context):
            raise ValueError("Invalid or duplicate exposure context record")
        metadata = {"reachability": state, "reachability_source": "supplied"}
        if "relationships" in row:
            metadata["relationships"] = read_relationships(row["relationships"])
        context[component, rule] = metadata
    return context, sha256(data).hexdigest()


def prioritize(report, context):
    groups = {}
    for component in report["components"]:
        for finding in component.get("findings", []):
            key = component["name"], finding["rule"]
            rank = SEVERITY.get(finding["severity"], 0)
            if key not in groups or rank > SEVERITY.get(groups[key]["severity"], 0):
                groups[key] = finding
    queue = [
        {"component": component, "rule": rule, "severity": finding["severity"],
         "owner": finding["owner"], **context.get((component, rule), {
             "reachability": "unknown", "reachability_source": "unavailable",
         })}
        for (component, rule), finding in groups.items()
    ]
    queue.sort(key=lambda row: (
        -SEVERITY.get(row["severity"], 0), -REACHABILITY[row["reachability"]],
        row["component"], row["rule"],
    ))
    return queue
