import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class PrioritizationTest(unittest.TestCase):
    def test_context_is_advisory_and_requires_matching_revision(self):
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "report.json"
            for revision, status in (("1" * 40, "complete"), ("2" * 40, "error")):
                with self.subTest(status=status):
                    command = subprocess.run([
                        sys.executable, "-m", "cyberops", "--root", "examples/before",
                        "--inventory", "examples/components.json", "--candidate-revision", revision,
                        "--exposure-context", "examples/exposure-context/reachability.json",
                        "--report", str(report),
                    ], capture_output=True, text=True)
                    self.assertEqual(command.returncode, 1)
                    result = json.loads(report.read_text())
                    self.assertEqual(result["decision"], "block")
                    self.assertEqual(result["triage"]["status"], status)
                    first, second = result["triage"]["queue"]
                    self.assertEqual(first["rule"], "EXPLICIT_USER")
                    self.assertEqual(first["reachability"], "unknown")
                    self.assertEqual(second["reachability"],
                                     "reachable" if status == "complete" else "unknown")
