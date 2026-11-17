import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from cyberops.harness import Harness
from cyberops.learning import apply_learning

COMPONENT = {"name": "service", "owner": "platform", "dockerfile": "Dockerfile"}


class HarnessTest(unittest.TestCase):
    def test_registered_skill_and_model_share_a_provider_neutral_contract(self):
        class Model:
            def explain(self, findings):
                return f"Review {findings[0][0]}"

        harness = Harness(red=(lambda _: [("EXPLICIT_USER", 1)],), model=Model())
        with ThreadPoolExecutor() as pool:
            findings = harness.assess(b"FROM scratch\nUSER 10", COMPONENT, {}, pool)
        result = harness.evaluate(findings, set())
        self.assertEqual(result["purple"]["decision"], "block")
        self.assertEqual(result["advisory"], "Review EXPLICIT_USER")

    def test_learning_cannot_modify_the_gate(self):
        def learning(_, verdict):
            verdict["decision"] = "pass"
            return []

        result = Harness(purple_learning=learning).evaluate(
            [{"rule": "EXPLICIT_USER", "severity": "critical"}], set()
        )
        self.assertEqual(result["purple"]["decision"], "block")

    def test_approved_lesson_becomes_a_required_check(self):
        harness = Harness()
        lesson = harness.evaluate([], {"CI.guardrail"})["lessons"][0]
        with tempfile.TemporaryDirectory() as directory:
            policy = Path(directory) / "learning.json"
            policy.write_text(json.dumps([
                {"component": "service", "check": lesson["suggested_required_check"]},
            ]))
            component = apply_learning([COMPONENT], policy)[0]
        with ThreadPoolExecutor() as pool:
            with self.assertRaisesRegex(ValueError, "guardrail is missing"):
                harness.assess(b"FROM scratch\nUSER 10", component, {}, pool)
            findings = harness.assess(
                b"FROM scratch\nUSER 10", component, {("service", "guardrail"): "pass"}, pool
            )
        self.assertEqual(harness.evaluate(findings, set())["purple"]["decision"], "pass")
