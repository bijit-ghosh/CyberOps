import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class ReportPublicationTest(unittest.TestCase):
    def test_malformed_inventory_publishes_error_and_replaces_previous_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inventory = root / "inventory.json"
            inventory.write_text("[" * 2000)
            report = root / "report.json"
            report.write_text('{"decision":"pass"}')
            result = subprocess.run([
                sys.executable, "-m", "cyberops", "--root", "examples/after",
                "--inventory", str(inventory), "--report", str(report),
            ], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(report.read_text())["decision"], "error")
            self.assertEqual(sorted(p.name for p in root.iterdir()), ["inventory.json", "report.json"])
