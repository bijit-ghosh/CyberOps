"""Collect reviewed CI findings for advisory defensive learning."""

import argparse
import json
import sqlite3
from contextlib import closing
from hashlib import sha256
from pathlib import Path

from .evidence import IDENTIFIER, REVISION

MAX_REPORT_BYTES = 1_000_000
REVIEW_LABELS = ("standard", "priority")


def read_findings(path):
    with path.open("rb") as stream:
        data = stream.read(MAX_REPORT_BYTES + 1)
    if len(data) > MAX_REPORT_BYTES:
        raise ValueError("Report exceeds size limit")
    report = json.loads(data)
    if not isinstance(report, dict) or report.get("schema_version") != 1:
        raise ValueError("Expected a CyberOps decision report")
    revision = report.get("candidate_revision")
    if not isinstance(revision, str) or not REVISION.fullmatch(revision):
        raise ValueError("A candidate revision is required")
    policy = report.get("effective_policy_sha256")
    if not isinstance(policy, str) or len(policy) != 64 or any(c not in "0123456789abcdef" for c in policy):
        raise ValueError("An effective policy digest is required")
    if report.get("decision") not in ("pass", "block") or not isinstance(report.get("components"), list):
        raise ValueError("A completed decision is required")
    entries = set()
    for component in report["components"]:
        if not isinstance(component, dict) or not isinstance(component.get("findings"), list):
            raise ValueError("Invalid component findings")
        name = component.get("name")
        if not isinstance(name, str) or not IDENTIFIER.fullmatch(name):
            raise ValueError("Invalid component identifier")
        for finding in component["findings"]:
            rule = finding.get("rule") if isinstance(finding, dict) else None
            if not isinstance(rule, str) or not IDENTIFIER.fullmatch(rule):
                raise ValueError("Invalid finding rule identifier")
            case_id = sha256(f"{revision}:{policy}:{name}:{rule}".encode()).hexdigest()
            entries.add((case_id, revision, policy, name, rule))
    return sorted(entries)


def open_ledger(path):
    database = sqlite3.connect(path)
    try:
        database.execute("""
            CREATE TABLE IF NOT EXISTS cases (
                id TEXT PRIMARY KEY,
                revision TEXT NOT NULL,
                policy TEXT NOT NULL,
                component TEXT NOT NULL,
                control TEXT NOT NULL,
                review TEXT CHECK (review IN ('standard', 'priority')),
                reviewer TEXT
            )
        """)
        database.execute("CREATE INDEX IF NOT EXISTS cases_policy_review ON cases(policy, review)")
    except sqlite3.Error:
        database.close()
        raise
    return database


def insert_findings(database, entries):
    cursor = database.executemany(
        """INSERT INTO cases(id, revision, policy, component, control)
           VALUES (?, ?, ?, ?, ?) ON CONFLICT(id) DO NOTHING""",
        entries,
    )
    return cursor.rowcount


def ingest(database, path):
    entries = read_findings(path)
    with database:
        return insert_findings(database, entries)


def record_review(database, case_id, reviewer, label):
    if not IDENTIFIER.fullmatch(reviewer) or label not in REVIEW_LABELS:
        raise ValueError("Invalid reviewer identifier or review label")
    with database:
        cursor = database.execute(
            "UPDATE cases SET review = ?, reviewer = ? WHERE id = ? AND review IS NULL",
            (label, reviewer, case_id),
        )
        if cursor.rowcount != 1:
            raise ValueError("Case is unknown or already reviewed")


def pending(database, *, policy=None):
    query = "SELECT id, revision, component, control FROM cases WHERE review IS NULL"
    args = ()
    if policy is not None:
        query += " AND policy = ?"
        args = (policy,)
    return [
        {"id": case, "revision": revision, "component": component, "control": control}
        for case, revision, component, control in database.execute(query + " ORDER BY id", args)
    ]


def validate_policy(policy):
    if len(policy) != 64 or any(c not in "0123456789abcdef" for c in policy):
        raise ValueError("An effective policy digest is required")


def replay_rows(database, policy):
    validate_policy(policy)
    return [
        {"id": case, "control": control, "review": review}
        for case, control, review in database.execute(
            "SELECT id, control, review FROM cases WHERE policy = ? AND review IS NOT NULL ORDER BY id",
            (policy,),
        )
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True, type=Path)
    commands = parser.add_subparsers(dest="command", required=True)
    ingest_parser = commands.add_parser("ingest")
    ingest_parser.add_argument("report", type=Path)
    commands.add_parser("pending")
    review_parser = commands.add_parser("review")
    review_parser.add_argument("case_id")
    review_parser.add_argument("--reviewer", required=True)
    review_parser.add_argument("--label", required=True, choices=REVIEW_LABELS)
    export_parser = commands.add_parser("export")
    export_parser.add_argument("--policy", required=True)
    args = parser.parse_args()
    try:
        with closing(open_ledger(args.db)) as database:
            if args.command == "ingest":
                output = {"inserted": ingest(database, args.report)}
            elif args.command == "pending":
                output = pending(database)
            elif args.command == "review":
                record_review(database, args.case_id, args.reviewer, args.label)
                output = {"reviewed": args.case_id}
            else:
                output = replay_rows(database, args.policy)
        print(json.dumps(output, indent=2))
    except (OSError, sqlite3.Error, ValueError, RecursionError) as error:
        parser.exit(2, f"Ledger error: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
