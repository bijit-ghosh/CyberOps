import json
import tempfile
import unittest
from contextlib import closing
from hashlib import sha256
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from cyberops.ledger import open_ledger
from cyberops.platform.server import credentials, handler_for
from cyberops.platform.service import ConsoleService


class ConsoleTest(unittest.TestCase):
    def test_review_workflow_and_role_enforcement(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report, database = root / "report.json", root / "ledger.db"
            policy, viewer, reviewer = "1" * 64, "v" * 32, "r" * 32
            report.write_text(json.dumps({
                "schema_version": 1, "decision": "block",
                "candidate_revision": "2" * 40, "effective_policy_sha256": policy,
                "components": [{"name": "service", "findings": [{"rule": "IMAGE_PIN"}]}],
            }))
            access = credentials(json.dumps({
                "observer": {"role": "viewer", "sha256": sha256(viewer.encode()).hexdigest()},
                "analyst": {"role": "reviewer", "sha256": sha256(reviewer.encode()).hexdigest()},
            }))
            with ThreadingHTTPServer(("127.0.0.1", 0), handler_for(
                ConsoleService(report, database), access
            )) as server:
                thread = Thread(target=server.serve_forever, daemon=True)
                thread.start()

                def request(path, token="", body=None):
                    with closing(HTTPConnection("127.0.0.1", server.server_port, timeout=5)) as client:
                        method = "GET" if body is None else "POST"
                        client.request(method, path, body=None if body is None else json.dumps(body),
                                       headers={"Authorization": "Bearer " + token,
                                                "Content-Type": "application/json"})
                        response = client.getresponse()
                        return response.status, response.read(), response.headers

                try:
                    status, page, headers = request("/")
                    self.assertEqual(status, 200)
                    self.assertIn(b"Release overview", page)
                    self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])
                    self.assertEqual(request("/api/v1/overview")[0], 401)
                    self.assertEqual(request("/api/v1/import", viewer, {})[0], 403)
                    self.assertEqual(json.loads(request("/api/v1/import", reviewer, {})[1])["imported"], 1)
                    self.assertEqual(json.loads(request("/api/v1/import", reviewer, {})[1])["imported"], 0)
                    snapshot = json.loads(request("/api/v1/overview", viewer)[1])
                    case, = snapshot["queue"]
                    payload = {"id": case["id"], "label": "priority", "policy": policy}
                    self.assertEqual(request("/api/v1/reviews", reviewer, {**payload, "policy": "0" * 64})[0], 400)
                    self.assertEqual(request("/api/v1/reviews", reviewer, payload)[0], 200)
                    self.assertEqual(request("/api/v1/reviews", reviewer, payload)[0], 400)
                    self.assertEqual(json.loads(request("/api/v1/overview", viewer)[1])["queue"], [])
                    with closing(open_ledger(database)) as ledger:
                        self.assertEqual(ledger.execute("SELECT review, reviewer FROM cases").fetchone(),
                                         ("priority", "analyst"))
                finally:
                    server.shutdown()
                    thread.join()
