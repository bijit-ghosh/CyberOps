import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "examples/evidence"


class EvidenceGateTest(unittest.TestCase):
    def assess(self, candidate, revision="2" * 40):
        with tempfile.TemporaryDirectory() as temp:
            evidence = Path(temp) / "candidate.json"
            evidence.write_text(json.dumps(candidate))
            report = Path(temp) / "report.json"
            result = subprocess.run([
                sys.executable, "-m", "cyberops", "--root", "examples/after",
                "--baseline-root", "examples/before",
                "--inventory", str(EVIDENCE / "components.json"),
                "--evidence", str(evidence), "--revision", revision,
                "--baseline-evidence", str(EVIDENCE / "before.json"),
                "--baseline-revision", "1" * 40, "--report", str(report),
            ], cwd=ROOT, capture_output=True, text=True)
            return result.returncode, json.loads(report.read_text())

    def setUp(self):
        self.candidate = json.loads((EVIDENCE / "after.json").read_text())

    def test_resolved_check_creates_regression_lesson(self):
        status, report = self.assess(self.candidate)
        self.assertEqual(status, 0)
        component = report["components"][0]
        self.assertIn("CI.dependency-policy", component["purple"]["resolved_rules"])
        self.assertIn("CI.dependency-policy", [lesson["rule"] for lesson in component["lessons"]])

    def test_failed_check_blocks_and_remains_open(self):
        self.candidate["checks"][0]["status"] = "fail"
        status, report = self.assess(self.candidate)
        self.assertEqual(status, 1)
        component = report["components"][0]
        self.assertEqual(component["purple"]["persistent_rules"], ["CI.dependency-policy"])
        self.assertEqual(component["findings"][0]["owner"], "platform-security")

    def test_missing_check_fails_closed(self):
        self.candidate["checks"].pop()
        status, report = self.assess(self.candidate)
        self.assertEqual((status, report["decision"]), (2, "error"))

    def test_mismatched_revision_fails_closed(self):
        status, report = self.assess(self.candidate, revision="3" * 40)
        self.assertEqual((status, report["decision"]), (2, "error"))
