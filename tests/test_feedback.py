import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from cyberops.feedback import cycle
from cyberops.ledger import open_ledger, record_review


class FeedbackTest(unittest.TestCase):
    def test_gate_to_review_to_evaluation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = root / "ci.json"
            command = subprocess.run([
                sys.executable, "-m", "cyberops", "--root", "examples/before",
                "--inventory", "examples/components.json", "--candidate-revision", "1" * 40,
                "--report", str(report),
            ], capture_output=True, text=True)
            self.assertEqual(command.returncode, 1)
            policy = json.loads(report.read_text())["effective_policy_sha256"]
            db = root / "ledger.db"
            with closing(open_ledger(db)) as ledger:
                self.assertEqual(cycle(ledger, policy)["stage"], "evidence_required")
                first = cycle(ledger, policy, [report])
                self.assertEqual((first["stage"], first["imported"]), ("review_required", 2))
                for finding in first["pending"]:
                    record_review(ledger, finding["id"], "test-reviewer", "priority")

            with closing(open_ledger(db)) as ledger:
                self.assertEqual(cycle(ledger, policy)["stage"], "holdout_required")
                holdout = root / "holdout.json"
                holdout.write_text(json.dumps([
                    {"id": "holdout", "control": "IMAGE_PIN", "review": "priority"}
                ]))
                checked = cycle(ledger, policy, [report], holdout)
                self.assertEqual((checked["stage"], checked["imported"]), ("evaluated", 0))
                self.assertEqual(checked["evaluation"]["fallbacks"], 1)
                self.assertEqual(cycle(ledger, "0" * 64)["stage"], "evidence_required")
