import json
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from cyberops.ledger import ingest, open_ledger, pending, record_review, replay_rows


class LedgerTest(unittest.TestCase):
    def test_review_feedback_survives_retries_and_restart(self):
        policy = "1" * 64
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = root / "report.json"
            report.write_text(json.dumps({
                "schema_version": 1, "candidate_revision": "a" * 40,
                "effective_policy_sha256": policy, "decision": "block",
                "components": [{"name": "service", "findings": [
                    {"rule": "IMAGE_PIN", "untrusted_detail": "not retained"},
                    {"rule": "IMAGE_PIN"},
                ]}],
            }))
            path = root / "ledger.db"
            with closing(open_ledger(path)) as ledger:
                self.assertEqual(ingest(ledger, report), 1)
                case = pending(ledger)[0]
                self.assertEqual(replay_rows(ledger, policy), [])
                record_review(ledger, case["id"], "analyst", "priority")
            with closing(open_ledger(path)) as ledger:
                self.assertEqual(ingest(ledger, report), 0)
                self.assertEqual(pending(ledger), [])
                self.assertEqual(replay_rows(ledger, policy), [{
                    "id": case["id"], "control": "IMAGE_PIN", "review": "priority",
                }])
                self.assertEqual(replay_rows(ledger, "2" * 64), [])
                with self.assertRaises(ValueError):
                    record_review(ledger, case["id"], "analyst", "standard")
