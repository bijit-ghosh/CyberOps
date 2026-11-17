import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from cyberops.evidence import load_evidence


@unittest.skipUnless(shutil.which("openssl"), "OpenSSL is required for optional signed evidence")
class SignedEvidenceTest(unittest.TestCase):
    def test_verified_bytes_are_bound_to_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            key, public, signature = (root / name for name in ("key.pem", "public.pem", "report.sig"))
            evidence = root / "evidence.json"
            evidence.write_bytes(Path("examples/evidence/after.json").read_bytes())
            for command in (
                ["genpkey", "-algorithm", "ED25519", "-out", str(key)],
                ["pkey", "-in", str(key), "-pubout", "-out", str(public)],
                ["pkeyutl", "-sign", "-inkey", str(key), "-rawin", "-in", str(evidence),
                 "-out", str(signature)],
            ):
                subprocess.run(["openssl", *command], capture_output=True, check=True)
            _, metadata = load_evidence(evidence, "2" * 40, signature=signature, public_key=public)
            self.assertTrue(metadata["signature_verified"])
            with self.assertRaisesRegex(ValueError, "revision"):
                load_evidence(evidence, "3" * 40, signature=signature, public_key=public)
            evidence.write_bytes(evidence.read_bytes().replace(b'"pass"', b'"fail"', 1))
            with self.assertRaisesRegex(ValueError, "verification failed"):
                load_evidence(evidence, "2" * 40, signature=signature, public_key=public)
