"""Connect a trusted release report to the Purple review workflow."""

import json
from contextlib import closing

from ..ledger import MAX_REPORT_BYTES, insert_findings, open_ledger, parse_findings, pending, record_review


class ConsoleService:
    def __init__(self, report_path, database_path):
        self.report_path = report_path
        self.database_path = database_path

    def report(self):
        try:
            with self.report_path.open("rb") as source:
                data = source.read(MAX_REPORT_BYTES + 1)
        except FileNotFoundError:
            return None
        if len(data) > MAX_REPORT_BYTES:
            raise ValueError("Report exceeds console size limit")
        result = json.loads(data)
        if (not isinstance(result, dict) or result.get("schema_version") != 1
                or result.get("decision") not in ("pass", "block", "error")):
            raise ValueError("Invalid release report")
        return result

    def overview(self):
        report = self.report()
        policy = report.get("effective_policy_sha256") if report else None
        queue = []
        if policy:
            with closing(open_ledger(self.database_path)) as database:
                queue = pending(database, policy=policy)
        return {"report": report, "queue": queue}

    def import_current(self):
        report = self.report()
        if report is None:
            raise ValueError("A completed CI report is required")
        entries = parse_findings(report)
        with closing(open_ledger(self.database_path)) as database, database:
            return insert_findings(database, entries)

    def review(self, case, label, actor, policy):
        current = self.report()
        if not current or current.get("effective_policy_sha256") != policy:
            raise ValueError("Refresh the console before reviewing this case")
        with closing(open_ledger(self.database_path)) as database:
            record_review(database, case, actor, label, policy=policy)
