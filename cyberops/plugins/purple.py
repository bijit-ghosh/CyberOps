"""Verify findings and propose regression checks for owner review."""

from copy import deepcopy

from ..skills import purple_learning, purple_verify


def verify(findings, previous=(), *, learn=purple_learning):
    verdict = purple_verify(findings, set(previous))
    return {"purple": verdict, "lessons": learn(deepcopy(findings), deepcopy(verdict))}
