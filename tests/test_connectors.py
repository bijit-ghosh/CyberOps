import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cyberops.connectors import junit_status


class ConnectorTest(unittest.TestCase):
    def test_export_feeds_release_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            junit = root / "tests.xml"
            junit.write_text('<testsuite><testcase name="verified"/></testsuite>')
            evidence = root / "evidence.json"
            report = root / "report.json"
            revision = "2" * 40
            subprocess.run([
                sys.executable, "-m", "cyberops.connectors", "--revision", revision,
                "--component", "example-service", "--status", "dependency-policy", "pass",
                "--junit", "guardrail-regression", str(junit), "--output", str(evidence),
            ], check=True)
            subprocess.run([
                sys.executable, "-m", "cyberops", "--root", "examples/after",
                "--inventory", "examples/evidence/components.json", "--revision", revision,
                "--evidence", str(evidence), "--report", str(report),
            ], check=True, capture_output=True)
            self.assertEqual(json.loads(report.read_text())["metrics"]["required_check_results"]["pass"], 2)

    def test_incomplete_and_failed_suite(self):
        with tempfile.TemporaryDirectory() as directory:
            junit = Path(directory) / "tests.xml"
            for result, status in (("skipped", "error"), ("failure", "fail"), ("error", "error")):
                with self.subTest(result=result):
                    junit.write_text(f"<testsuite><testcase><{result}/></testcase></testsuite>")
                    self.assertEqual(junit_status(junit), status)
            junit.write_text("<testsuite/>")
            with self.assertRaisesRegex(ValueError, "no tests"):
                junit_status(junit)
