"""Review build controls and completed defensive CI results."""

from ..evidence import review_checks
from ..skills import instructions, red_runtime_identity, red_supply_chain

REVIEWERS = (red_supply_chain, red_runtime_identity)


def review(content, reviewers=REVIEWERS, pool=None):
    parsed = tuple(instructions(content))
    if pool is None:
        return [item for reviewer in reviewers for item in reviewer(parsed)]
    jobs = [pool.submit(reviewer, parsed) for reviewer in reviewers]
    return [item for job in jobs for item in job.result()]
