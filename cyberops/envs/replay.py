"""Evaluate advisory defensive routing on reviewed and held-out synthetic data."""

import argparse
import json
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path

from ..evidence import IDENTIFIER

MAX_BYTES = 256_000
LABELS = {"standard", "priority"}


def read_cases(path):
    with path.open("rb") as stream:
        data = stream.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("Replay dataset exceeds size limit")
    cases = json.loads(data)
    if not isinstance(cases, list) or not cases:
        raise ValueError("Replay dataset must contain labeled cases")
    ids = set()
    for row in cases:
        if not isinstance(row, dict) or set(row) != {"id", "control", "review"}:
            raise ValueError("Each case requires id, control and review")
        if any(not isinstance(value, str) or not IDENTIFIER.fullmatch(value)
               for value in row.values()):
            raise ValueError("Replay fields must be identifiers")
        if row["id"] in ids or row["review"] not in LABELS:
            raise ValueError("Duplicate case ID or unsupported review outcome")
        ids.add(row["id"])
    return cases, sha256(data).hexdigest()


def evaluate(training, held_out):
    if {row["id"] for row in training} & {row["id"] for row in held_out}:
        raise ValueError("Training and evaluation case IDs overlap")
    counts = defaultdict(Counter)
    for row in training:
        counts[row["control"]][row["review"]] += 1

    results = []
    for row in held_out:
        support = counts.get(row["control"], Counter())
        total = support.total()
        # With sparse or conflicting evidence, route to deterministic human review.
        reason = "unseen_control" if total == 0 else "insufficient_consensus"
        recommendation = "manual_review"
        if total >= 3:
            label, votes = support.most_common(1)[0]
            if votes * 5 >= total * 4:
                reason, recommendation = "reviewed_history_consensus", label
        results.append({
            "id": row["id"], "control": row["control"], "expected": row["review"],
            "recommendation": recommendation, "reason": reason, "support": dict(support),
        })
    automated = [row for row in results if row["recommendation"] != "manual_review"]
    return {
        "evaluated": len(results),
        "recommendations": len(automated),
        "correct_recommendations": sum(row["expected"] == row["recommendation"] for row in automated),
        "fallbacks": len(results) - len(automated),
        "missed_priority": sum(row["expected"] == "priority" and row["recommendation"] == "standard"
                               for row in automated),
        "cases": results,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--training", type=Path, required=True)
    parser.add_argument("--held-out", type=Path, required=True)
    args = parser.parse_args()
    try:
        training, training_digest = read_cases(args.training)
        held_out, evaluation_digest = read_cases(args.held_out)
        report = evaluate(training, held_out)
        print(json.dumps({"schema_version": 1, "training_sha256": training_digest,
                          "evaluation_sha256": evaluation_digest, **report}, indent=2))
    except (OSError, ValueError, RecursionError) as error:
        parser.exit(2, f"Replay error: {error}\n")


if __name__ == "__main__":
    main()
