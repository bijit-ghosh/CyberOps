"""Built-in defensive skills used by the CyberOps harness."""

import re

RULES = {
    "IMAGE_PIN": (
        "high", "Unpinned base image makes builds depend on a mutable registry reference.",
        "Pin the trusted base image to a reviewed sha256 digest."
    ),
    "EXPLICIT_USER": (
        "critical", "Final stage does not declare an explicit numeric non-root user.",
        "Set USER to the application's verified nonzero numeric UID after the final FROM."
    ),
}


def instructions(content):
    """Parse a limited Dockerfile subset and fail closed on unsupported syntax."""
    parsed = []
    for number, raw in enumerate(content.decode().splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            if re.match(r"#\s*(escape|syntax)\s*=", line, re.I):
                raise ValueError("Dockerfile parser directives require manual review")
            continue
        if "\\" in line or "<<" in line or "\x00" in line:
            raise ValueError(f"Unsupported Dockerfile syntax at line {number}")
        parts = line.split(maxsplit=1)
        if len(parts) != 2 or not re.fullmatch(r"[A-Za-z]+", parts[0]):
            raise ValueError(f"Invalid Dockerfile instruction at line {number}")
        parsed.append((number, parts[0].upper(), parts[1]))
    if not any(op == "FROM" for _, op, _ in parsed):
        raise ValueError("Dockerfile has no FROM instruction")
    return parsed


def red_supply_chain(parsed):
    aliases = set()
    observations = []
    for line, op, arg in parsed:
        if op != "FROM":
            continue
        match = re.fullmatch(r"(?:--platform=\S+\s+)?([^\s]+)(?:\s+AS\s+([\w.-]+))?", arg, re.I)
        if not match:
            raise ValueError(f"Unsupported FROM instruction at line {line}")
        image, alias = match.groups()
        if image.lower() not in aliases and image.lower() != "scratch" and not re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9./:_-]*@sha256:[0-9a-f]{64}", image
        ):
            observations.append(("IMAGE_PIN", line))
        if alias:
            aliases.add(alias.lower())
    return observations


def red_runtime_identity(parsed):
    final_from = max(line for line, op, _ in parsed if op == "FROM")
    users = [(line, arg) for line, op, arg in parsed if op == "USER" and line > final_from]
    line, user = users[-1] if users else (final_from, "")
    if not re.fullmatch(r"[1-9][0-9]{0,9}(?::[0-9]{1,10})?", user):
        return [("EXPLICIT_USER", line)]
    uid, _, gid = user.partition(":")
    if int(uid) >= 2**32 - 1 or (gid and int(gid) >= 2**32 - 1):
        return [("EXPLICIT_USER", line)]
    return []


def blue_triage(component, findings):
    return [
        {"rule": rule, "line": line, "severity": RULES[rule][0], "risk": RULES[rule][1],
         "owner": component["owner"]}
        for rule, line in sorted(findings, key=lambda item: item[1])
    ]


def blue_remediation(findings):
    return [{**finding, "remediation": RULES[finding["rule"]][2]} for finding in findings]


def purple_verify(findings, previous):
    current = {finding["rule"] for finding in findings}
    return {
        "decision": "block" if findings else "pass",
        "resolved_rules": sorted(previous - current),
        "new_rules": sorted(current - previous),
        "persistent_rules": sorted(current & previous),
    }


def purple_learning(findings, verdict):
    resolved = set(verdict["resolved_rules"])
    return [
        {"rule": rule, "lesson": (
             RULES[rule][2] if rule in RULES
             else f"Keep {rule.removeprefix('CI.')} as a required CI regression check."
         ),
         "promotion": "owner review required",
         **({"suggested_required_check": rule.removeprefix("CI.")}
            if rule in resolved and rule.startswith("CI.") else {}),
         "validation": "Build and run authorized functional tests before releasing"}
        for rule in sorted({finding["rule"] for finding in findings} | set(verdict["resolved_rules"]))
    ]


