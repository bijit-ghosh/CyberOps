"""Apply approved regression requirements from versioned policy."""

import json

from .evidence import IDENTIFIER


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
