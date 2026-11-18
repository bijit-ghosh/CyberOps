"""Run the synthetic AI guardrail demo and retain both decision reports."""

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT / "ai-guardrail"
RECIPE = ROOT / "after"
CONTROL = "tool-output-sanitization"
RULE = f"CI.{CONTROL}"


def assess(output, revision, source, expected_exit, *extra):
    destination = output / f"{source}.json"
    result = subprocess.run([
        sys.executable, "-m", "cyberops", "--root", str(RECIPE),
        "--inventory", str(FIXTURE / "components.json"),
        "--candidate-revision", revision, "--revision", revision,
        "--evidence", str(FIXTURE / f"{source}.json"), "--report", str(destination),
        *extra,
    ], check=False, capture_output=True, text=True)
    if result.returncode != expected_exit:
        raise ValueError(f"{source}: expected exit {expected_exit}, got {result.returncode}. "
                         + result.stderr.strip())
    return json.loads(destination.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, help="Directory for before.json and after.json")
    args = parser.parse_args()
    try:
        output = args.output_dir or Path(tempfile.mkdtemp(prefix="cyberops-quickstart-"))
        output.mkdir(parents=True, exist_ok=True)
        if any((output / f"{name}.json").exists() for name in ("before", "after")):
            raise ValueError("Choose an output directory without existing before.json or after.json files")
        blocked = assess(output, "1" * 40, "before", 1,
                         "--exposure-context", str(FIXTURE / "context.json"))
        passed = assess(output, "2" * 40, "after", 0,
                        "--baseline-root", str(RECIPE), "--baseline-revision", "1" * 40,
                        "--baseline-evidence", str(FIXTURE / "before.json"))
        finding, = blocked["triage"]["queue"]
        component, = passed["components"]
        if (blocked["decision"] != "block" or finding["rule"] != RULE or not finding["relationships"]
                or passed["decision"] != "pass" or RULE not in component["purple"]["resolved_rules"]
                or not any(item.get("suggested_required_check") == CONTROL for item in component["lessons"])):
            raise ValueError("Demo reports do not show the expected block, fix, and lesson")
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(2, f"Quickstart failed: {error}\n")
    print(f"Blocked: {RULE} · owner {finding['owner']}")
    print(f"Verified fix: {RULE}")
    print(f"Proposed regression check: {CONTROL}")
    print(f"Reports: {output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
