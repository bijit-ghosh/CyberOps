"""Typed envelopes and bounded asynchronous transit for the local simulator."""

import asyncio
import re
from dataclasses import dataclass
from typing import Literal

Team = Literal["red", "blue", "purple"]
State = Literal["pass", "fail", "unknown", "block", "review"]
TEAM_STATES = {
    "red": {"pass", "fail", "unknown"},
    "blue": {"pass", "block", "review"},
    "purple": {"pass", "block", "review"},
}


@dataclass(frozen=True)
class Event:
    agent_id: str
    team: Team
    timestamp: int
    confidence: float
    control: str
    state: State

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[a-z][a-z0-9-]{0,63}", self.agent_id):
            raise ValueError("Invalid agent identifier")
        if self.state not in TEAM_STATES.get(self.team, set()):
            raise ValueError("Invalid state for team")
        if type(self.timestamp) is not int or self.timestamp < 0:
            raise ValueError("Invalid logical timestamp")
        if type(self.confidence) not in (float, int) or not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be between zero and one")
        if not re.fullmatch(r"[a-z][a-z0-9-]{0,63}", self.control):
            raise ValueError("Invalid control identifier")


class EventBus:
    def __init__(self, capacity: int = 4) -> None:
        if capacity < 1:
            raise ValueError("Event capacity must be positive")
        self.queue: asyncio.Queue[Event] = asyncio.Queue(maxsize=capacity)

    async def publish(self, event: Event) -> None:
        await asyncio.wait_for(self.queue.put(event), timeout=1)

    async def receive(self) -> Event:
        return await asyncio.wait_for(self.queue.get(), timeout=1)
