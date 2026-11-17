import asyncio
import unittest

from cyberops.swarms.events import Event
from cyberops.swarms.simulate import blue_decision, simulate


class SwarmSimulationTest(unittest.TestCase):
    def test_seeded_ten_step_smoke(self):
        first = asyncio.run(simulate(42, 10))
        self.assertEqual(first, asyncio.run(simulate(42, 10)))
        self.assertEqual(len(first["events"]), 30)
        self.assertEqual(sum(first["decisions"].values()), 10)
        self.assertEqual([event["team"] for event in first["events"][:3]],
                         ["red", "blue", "purple"])

    def test_fallback_and_schema(self):
        event = Event("red-reviewer", "red", 0, 0.5, "control", "pass")
        self.assertEqual(blue_decision(event), "review")
        with self.assertRaises(ValueError):
            Event("red-reviewer", "red", 0, float("nan"), "control", "pass")
