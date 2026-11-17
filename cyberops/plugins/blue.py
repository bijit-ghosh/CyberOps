"""Enrich control observations with risk, ownership and remediation."""

from ..skills import blue_remediation, blue_triage


def remediate(component, observations, *, triage=blue_triage, remediation=blue_remediation):
    return remediation(triage(component, observations))
