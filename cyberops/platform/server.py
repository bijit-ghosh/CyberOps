"""Serve the local CyberOps operator console and its same-origin API."""

import argparse
import hmac
import json
import os
import re
import sqlite3
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from pathlib import Path

from ..evidence import IDENTIFIER
from .service import ConsoleService

MAX_BODY = 4096
HEX = re.compile(r"[0-9a-f]{64}")
STATIC = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
}


def credentials(raw):
    entries = json.loads(raw)
    if not isinstance(entries, dict) or not entries:
        raise ValueError("Configure at least one console credential")
    result = {}
    for actor, entry in entries.items():
        if (not IDENTIFIER.fullmatch(actor) or not isinstance(entry, dict)
                or set(entry) != {"role", "sha256"} or entry["role"] not in ("viewer", "reviewer")
                or not isinstance(entry["sha256"], str) or not HEX.fullmatch(entry["sha256"])
                or entry["sha256"] in result):
            raise ValueError("Invalid console credential")
        result[entry["sha256"]] = (actor, entry["role"])
    return result


def handler_for(service, authorized):
    class Handler(BaseHTTPRequestHandler):
        def send_payload(self, status, data, content_type):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", (
                "default-src 'none'; script-src 'self'; style-src 'self'; "
                "connect-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
            ))
            self.end_headers()
            self.wfile.write(data)

        def respond(self, status, payload):
            self.send_payload(status, json.dumps(payload).encode(), "application/json")

        def identity(self, *, write=False):
            authorization = self.headers.get("Authorization", "")
            scheme, _, token = authorization.partition(" ")
            if scheme.lower() == "bearer" and 32 <= len(token) <= 256:
                digest = sha256(token.encode()).hexdigest()
                for expected, identity in authorized.items():
                    if hmac.compare_digest(expected, digest):
                        if write and identity[1] != "reviewer":
                            self.respond(403, {"error": "Reviewer access required"})
                            return None
                        return identity
            self.respond(401, {"error": "A valid console token is required"})
            return None

        def do_GET(self):
            if self.path in STATIC:
                name, content_type = STATIC[self.path]
                asset = files("cyberops.platform").joinpath("static", name)
                self.send_payload(200, asset.read_bytes(), content_type)
            elif self.path == "/api/v1/overview":
                identity = self.identity()
                if identity:
                    try:
                        self.respond(200, {**service.overview(), "role": identity[1]})
                    except (OSError, ValueError, RecursionError, sqlite3.Error):
                        self.respond(503, {"error": "Readiness report or review ledger unavailable"})
            else:
                self.respond(404, {"error": "Route not found"})

        def do_POST(self):
            if self.path not in ("/api/v1/import", "/api/v1/reviews"):
                self.respond(404, {"error": "Route not found"})
                return
            identity = self.identity(write=True)
            if not identity:
                return
            try:
                length = int(self.headers.get("Content-Length", "-1"))
                if not 0 < length <= MAX_BODY or self.headers.get_content_type() != "application/json":
                    raise ValueError("A bounded JSON request is required")
                body = json.loads(self.rfile.read(length))
                if self.path == "/api/v1/import" and body == {}:
                    self.respond(200, {"imported": service.import_current()})
                elif self.path == "/api/v1/reviews":
                    if (not isinstance(body, dict) or set(body) != {"id", "label", "policy"}
                            or any(not isinstance(body[key], str) or not HEX.fullmatch(body[key])
                                   for key in ("id", "policy")) or body["label"] not in ("standard", "priority")):
                        raise ValueError("Invalid review")
                    service.review(body["id"], body["label"], identity[0], body["policy"])
                    self.respond(200, {"reviewed": body["id"]})
                else:
                    raise ValueError("Unexpected request body")
            except (ValueError, RecursionError) as error:
                message = str(error) if not isinstance(error, (json.JSONDecodeError, UnicodeError)) else "Invalid JSON"
                self.respond(400, {"error": message})
            except (OSError, sqlite3.Error):
                self.respond(503, {"error": "Review ledger unavailable"})

        def setup(self):
            self.request.settimeout(10)
            super().setup()

    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    try:
        access = credentials(os.environ.get("CYBEROPS_CONSOLE_CREDENTIALS", "{}"))
        server = ThreadingHTTPServer(("127.0.0.1", args.port), handler_for(
            ConsoleService(args.report, args.db), access
        ))
    except (ValueError, OSError, OverflowError) as error:
        parser.exit(2, f"Cannot start CyberOps console: {error}\n")
    with server:
        print(f"CyberOps console at http://127.0.0.1:{server.server_port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
