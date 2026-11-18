// Receive a trusted CyberOps artifact in a Node.js release pipeline.
import { readFile } from "node:fs/promises";

const [path, expectedRevision] = process.argv.slice(2);
const exitFor = new Map([["pass", 0], ["block", 1], ["error", 2]]);

try {
  if (!path || expectedRevision?.length !== 40 || !/^[0-9a-f]+$/.test(expectedRevision)) {
    throw new Error("Usage: node read-report.mjs REPORT.json EXPECTED_SHA");
  }
  const report = JSON.parse(await readFile(path, "utf8"));
  if (report?.schema_version !== 1 || !exitFor.has(report.decision)) {
    throw new Error("Unsupported CyberOps report");
  }
  if (report.decision !== "error" && report.candidate_revision !== expectedRevision) {
    throw new Error("Report does not match the expected revision");
  }
  console.log(JSON.stringify({ decision: report.decision, revision: report.candidate_revision }));
  process.exitCode = exitFor.get(report.decision);
} catch (error) {
  console.error(error.message);
  process.exitCode = 2;
}
