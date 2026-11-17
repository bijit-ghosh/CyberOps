import unittest
from pathlib import Path

from cyberops.envs.replay import evaluate, read_cases

FIXTURES = Path(__file__).resolve().parents[1] / "examples/defensive-replay"


class ReplayTest(unittest.TestCase):
    def test_held_out_replay_explains_fallback(self):
        training, _ = read_cases(FIXTURES / "training.json")
        held_out, _ = read_cases(FIXTURES / "held-out.json")
        report = evaluate(training, held_out)
        self.assertEqual((report["recommendations"], report["fallbacks"]), (1, 2))
        self.assertEqual(report["correct_recommendations"], 1)
        self.assertEqual(report["missed_priority"], 0)
        self.assertEqual([row["reason"] for row in report["cases"]],
                         ["reviewed_history_consensus", "insufficient_consensus", "unseen_control"])
        with self.assertRaisesRegex(ValueError, "overlap"):
            evaluate(training, training)
