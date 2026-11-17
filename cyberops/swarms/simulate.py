"""Seeded simulation of defensive review handoffs, with no network actions."""

import argparse
import asyncio
import json
import random
from dataclasses import asdict

from .events import Event, EventBus, State

CONTROL = "build-control"


def blue_decision(observation: Event) -> State:
    if observation.state == "unknown" or observation.confidence < 0.8:
        return "review"
    return "block" if observation.state == "fail" else "pass"


async def simulate(seed: int, steps: int) -> dict[str, object]:
    if not 1 <= steps <= 1000:
        raise ValueError("Steps must be between 1 and 1000")
    rng = random.Random(seed)
    bus = EventBus()
    audit: list[dict[str, object]] = []
    counts = {"pass": 0, "block": 0, "review": 0}
    states: tuple[State, ...] = ("pass", "fail", "unknown")
    for step in range(steps):
        observation = Event("red-reviewer", "red", step * 3, rng.random(),
                            CONTROL, rng.choice(states))
        await bus.publish(observation)
        incoming = await bus.receive()
        decision = blue_decision(incoming)
        await bus.publish(Event("blue-reviewer", "blue", step * 3 + 1,
                                incoming.confidence, incoming.control, decision))
        handoff = await bus.receive()
        verified = blue_decision(observation)
        verdict: State = verified if verified == handoff.state else "review"
        final = Event("purple-verifier", "purple", step * 3 + 2,
                      handoff.confidence, handoff.control, verdict)
        counts[final.state] += 1
        audit.extend(asdict(event) for event in (observation, handoff, final))
    return {"schema_version": 1, "seed": seed, "steps": steps,
            "decisions": counts, "events": audit}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--steps", type=int, default=10)
    args = parser.parse_args()
    try:
        print(json.dumps(asyncio.run(simulate(args.seed, args.steps)), indent=2))
    except (ValueError, TimeoutError) as error:
        parser.exit(2, f"Simulation error: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
