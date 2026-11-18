"""Initiate or resume a defensive feedback cycle using trusted CI artifacts."""

import argparse
import json
import sqlite3
from contextlib import closing
from hashlib import sha256
from pathlib import Path

from .envs.replay import evaluate, read_cases
from .ledger import insert_findings, open_ledger, pending, read_findings, replay_rows, validate_policy


def cycle(database, policy, reports=(), held_out=None):
    # Validate the requested policy before importing any reports.
    validate_policy(policy)
    entries = [entry for report in reports for entry in read_findings(report)]
    if any(entry[2] != policy for entry in entries):
        raise ValueError("Report findings do not match the feedback policy")
    with database:
        database.execute("BEGIN")
        imported = insert_findings(database, entries) if entries else 0
        queue = pending(database, policy=policy)
        reviewed = replay_rows(database, policy)
    result = {
        "schema_version": 1,
        "policy": policy,
        "imported": imported,
        "pending": queue,
        "reviewed": len(reviewed),
    }
    if queue:
        return {**result, "stage": "review_required"}
    if not reviewed:
        return {**result, "stage": "evidence_required"}
    if held_out is None:
        return {**result, "stage": "holdout_required"}
    cases, digest = read_cases(held_out)
    training = json.dumps(reviewed, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        **result, "stage": "evaluated", "holdout_sha256": digest,
        "training_sha256": sha256(training).hexdigest(),
        "evaluation": evaluate(reviewed, cases),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True, type=Path)
    parser.add_argument("--policy", required=True)
    parser.add_argument("--report", type=Path, action="append", default=[])
    parser.add_argument("--held-out", type=Path)
    args = parser.parse_args()
    try:
        with closing(open_ledger(args.db)) as database:
            result = cycle(database, args.policy, args.report, args.held_out)
        print(json.dumps(result, indent=2))
    except (OSError, ValueError, sqlite3.Error, RecursionError) as error:
        parser.exit(2, f"Feedback cycle error: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
