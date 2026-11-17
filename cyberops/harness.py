"""Compose defensive skills without coupling them to a model provider."""

from dataclasses import dataclass
from typing import Callable, Protocol

from . import skills
from .plugins import blue, purple, red as red_plugin


class AdvisoryModel(Protocol):
    """Optional provider adapter for an explanatory note based on structured findings."""

    def explain(self, findings: tuple[tuple[str, str], ...]) -> str: ...


@dataclass(frozen=True)
class Harness:
    """Trusted callers register compatible callables when constructing the harness."""

    red: tuple[Callable, ...] = red_plugin.REVIEWERS
    red_ci: Callable = red_plugin.review_checks
    blue_triage: Callable = skills.blue_triage
    blue_remediation: Callable = skills.blue_remediation
    purple_learning: Callable = skills.purple_learning
    model: AdvisoryModel | None = None

    def review_ci(self, component, checks):
        return self.red_ci(component, checks)

    def assess(self, content, component, checks, pool=None):
        observations = red_plugin.review(content, self.red, pool)
        findings = blue.remediate(
            component, observations, triage=self.blue_triage, remediation=self.blue_remediation
        )
        if checks is not None:
            findings.extend(self.review_ci(component, checks))
        return findings

    def evaluate(self, findings, previous):
        result = purple.verify(findings, previous, learn=self.purple_learning)
        if self.model is not None and findings:
            try:
                note = self.model.explain(tuple((item["rule"], item["severity"]) for item in findings))
                if isinstance(note, str) and note.strip():
                    result["advisory"] = note[:2000]
                else:
                    result["advisory_status"] = "invalid"
            except Exception:
                result["advisory_status"] = "unavailable"
        return result
