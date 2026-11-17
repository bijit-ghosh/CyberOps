import json
import tempfile
import unittest
from pathlib import Path

from cyberops.learning import identify_recurring_findings
from cyberops.plugins import blue, purple, red
from cyberops.plugins.bundle import CyberOps


class PluginsTest(unittest.TestCase):
    def test_standalone_plugins_match_bundle(self):
        component = {"name": "service", "owner": "platform"}
        recipe = b"FROM python:3.12"
        findings = blue.remediate(component, red.review(recipe))
        bundle = CyberOps()
        self.assertEqual(findings, bundle.assess(recipe, component, {}))
        self.assertEqual(purple.verify(findings), bundle.evaluate(findings, set()))

    def test_history_flags_only_same_policy_previous_resolution(self):
        current = {
            "candidate_revision": "2" * 40, "effective_policy_sha256": "policy",
            "components": [{"name": "service", "findings": [{"rule": "IMAGE_PIN"}]}],
        }
        previous = {
            "schema_version": 1, "candidate_revision": "1" * 40,
            "effective_policy_sha256": "policy",
            "components": [{"name": "service", "purple": {
                "decision": "pass", "resolved_rules": ["IMAGE_PIN"],
            }}],
        }
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "history.json"
            report.write_text(json.dumps(previous))
            result = identify_recurring_findings(current, [report, report])
            self.assertEqual(result["historical_revisions"], 1)
            self.assertEqual(result["recurring_findings"][0]["rule"], "IMAGE_PIN")
            previous["effective_policy_sha256"] = "different"
            report.write_text(json.dumps(previous))
            self.assertEqual(identify_recurring_findings(current, [report])["recurring_findings"], [])
