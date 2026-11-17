"""Compose defensive skills without coupling them to a model provider."""

from copy import deepcopy
from dataclasses import dataclass
from typing import Callable, Protocol

from . import skills
from .evidence import review_checks


class AdvisoryModel(Protocol):
    """Optional provider adapter for an explanatory note based on structured findings."""

    def explain(self, findings: tuple[tuple[str, str], ...]) -> str: ...


@dataclass(frozen=True)
class Harness:
    """Trusted callers register compatible callables when constructing the harness."""

    red: tuple[Callable, ...] = (skills.red_supply_chain, skills.red_runtime_identity)
    red_ci: Callable = review_checks
    blue_triage: Callable = skills.blue_triage
    blue_remediation: Callable = skills.blue_remediation
    purple_learning: Callable = skills.purple_learning
    model: AdvisoryModel | None = None

    def review_ci(self, component, checks):
        return self.red_ci(component, checks)

    def assess(self, content, component, checks, pool):
        parsed = tuple(skills.instructions(content))
        jobs = [pool.submit(review, parsed) for review in self.red]
        observations = [observation for job in jobs for observation in job.result()]
        findings = self.blue_remediation(self.blue_triage(component, observations))
        if checks is not None:
            findings.extend(self.review_ci(component, checks))
        return findings

    def evaluate(self, findings, previous):
        verdict = skills.purple_verify(findings, previous)
        # Learning receives the evidence after verification and cannot alter the gate.
        learning = self.purple_learning(
            deepcopy(findings), deepcopy(verdict)
        )
        result = {"purple": verdict, "lessons": learning}
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
