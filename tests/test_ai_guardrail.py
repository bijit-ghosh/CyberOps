import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cyberops.summary import finding_id, render


class AIGuardrailTest(unittest.TestCase):
    def test_control_context_and_verified_fix(self):
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "report.json"
            fixture = Path("examples/ai-guardrail")
            command = [
                sys.executable, "-m", "cyberops", "--root", "examples/after",
                "--inventory", str(fixture / "components.json"), "--report", str(report),
            ]
            initial = command + ["--revision", "1" * 40, "--evidence", str(fixture / "before.json")]
            result = subprocess.run(
                initial + ["--exposure-context", str(fixture / "context.json")], capture_output=True
            )
            self.assertEqual(result.returncode, 1)
            blocked = json.loads(report.read_text())
            queued, = blocked["triage"]["queue"]
            summary = render(blocked)
            identifier = finding_id("partner-chatbot", "CI.tool-output-sanitization")
            self.assertIn(identifier, summary)
            self.assertIn("**Next step**", summary)
            self.assertIn("tool&#45;response&#45;boundary", summary)
            self.assertEqual(queued["owner"], "ai-platform")
            self.assertEqual(queued["reachability"], "unknown")
            self.assertEqual(len(queued["relationships"]), 3)
            blocked["triage"]["queue"][0]["owner"] = "[click](https://example.test)\n## Injected"
            self.assertNotIn("[click]", render(blocked))
            self.assertNotIn("\n## Injected", render(blocked))

            invalid_context = Path(directory) / "invalid.json"
            invalid = json.loads((fixture / "context.json").read_text())
            links = invalid["findings"][0]["relationships"]
            links.append(links[0])
            invalid_context.write_text(json.dumps(invalid))
            invalid_result = subprocess.run(
                initial + ["--exposure-context", str(invalid_context)], capture_output=True
            )
            self.assertEqual(invalid_result.returncode, 1)
            triage = json.loads(report.read_text())["triage"]
            self.assertEqual(triage["status"], "error")
            self.assertNotIn("relationships", triage["queue"][0])

            result = subprocess.run(command + [
                "--revision", "2" * 40, "--evidence", str(fixture / "after.json"),
                "--baseline-root", "examples/after", "--baseline-revision", "1" * 40,
                "--baseline-evidence", str(fixture / "before.json"),
            ], capture_output=True)
            self.assertEqual(result.returncode, 0)
            passed = json.loads(report.read_text())
            self.assertIn(identifier, render(passed))
            self.assertIn("**Regression proposal**", render(passed))
            component, = passed["components"]
            self.assertEqual(component["purple"]["resolved_rules"], ["CI.tool-output-sanitization"])
            self.assertEqual(component["lessons"][0]["suggested_required_check"],
                             "tool-output-sanitization")
