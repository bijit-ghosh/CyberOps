"use strict";

const el = (id) => document.getElementById(id);
let token = "";
let snapshot = null;
let generation = 0;

async function api(path, body) {
  const headers = { Authorization: "Bearer " + token };
  const options = { headers };
  if (body !== undefined) {
    options.method = "POST";
    headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }
  const response = await fetch("/api/v1/" + path, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error);
  return data;
}

function append(parent, tag, value) {
  const node = document.createElement(tag);
  node.textContent = value;
  parent.append(node);
  return node;
}

function findings() {
  const report = snapshot?.report;
  const target = el("findings");
  target.replaceChildren();
  const search = el("filter").value.trim().toLowerCase();
  const context = new Map((report?.triage?.queue ?? []).map(row =>
    [JSON.stringify([row.component, row.rule]), row]));
  for (const component of report?.components ?? []) {
    for (const finding of component.findings ?? []) {
      const label = [component.name, finding.rule, finding.owner, finding.severity].join(" · ");
      if (!label.toLowerCase().includes(search)) continue;
      const entry = document.createElement("details");
      append(entry, "summary", label);
      append(entry, "p", finding.risk);
      append(entry, "p", "Next step: " + finding.remediation);
      const row = context.get(JSON.stringify([component.name, finding.rule]));
      if (row) {
        append(entry, "p", "Reachability: " + row.reachability);
        for (const link of row.relationships ?? []) {
          append(entry, "p", link.relationship + " · " + link.target);
        }
      }
      target.append(entry);
    }
  }
  if (!target.childElementCount) append(target, "p", search ? "No matching findings." : "No open findings in the latest report.");
}

function render() {
  const { report, queue, role } = snapshot;
  const evidence = report?.metrics?.required_check_results;
  const total = evidence ? evidence.pass + evidence.fail + evidence.error + evidence.missing : 0;
  el("revision").textContent = report?.candidate_revision ?? "No candidate revision available";
  el("decision").textContent = report?.decision?.toUpperCase() ?? "—";
  el("decision").dataset.value = report?.decision ?? "";
  el("count").textContent = report?.components
    ? report.components.reduce((count, row) => count + (row.findings?.length ?? 0), 0) : "—";
  el("completeness").textContent = total ? (evidence.pass + evidence.fail) + " / " + total : "—";
  el("pending").textContent = queue.length;
  el("import").hidden = role !== "reviewer";
  el("import").disabled = !report?.candidate_revision || !["pass", "block"].includes(report.decision);
  findings();
  const target = el("queue");
  target.replaceChildren();
  if (!queue.length) append(target, "p", "No findings waiting for review under this policy.");
  for (const entry of queue) {
    const row = append(target, "div", "");
    row.className = "review";
    append(row, "span", entry.component + " · " + entry.control + " · " + entry.revision.slice(0, 12));
    if (role !== "reviewer") continue;
    for (const label of ["standard", "priority"]) {
      const button = append(row, "button", label === "priority" ? "Mark priority" : "Mark standard");
      button.className = "secondary";
      button.addEventListener("click", () => perform("Review recorded.", () =>
        api("reviews", { id: entry.id, label, policy: report.effective_policy_sha256 })));
    }
  }
}

async function refresh(message = "") {
  const active = ++generation;
  try {
    const data = await api("overview");
    if (active !== generation) return;
    snapshot = data;
    render();
    el("workspace").hidden = false;
    el("connect").hidden = true;
    el("status").textContent = message || (data.report ? "" : "No CI report has been published yet.");
  } catch (error) {
    if (active === generation) el("status").textContent = error.message;
  }
}

async function perform(message, action) {
  const active = generation;
  try {
    await action();
    if (active === generation) await refresh(message);
  } catch (error) {
    if (active === generation) el("status").textContent = error.message;
  }
}

el("connect").addEventListener("submit", (event) => {
  event.preventDefault();
  token = el("token").value;
  el("token").value = "";
  refresh();
});
el("disconnect").addEventListener("click", () => {
  generation++;
  token = "";
  snapshot = null;
  el("findings").replaceChildren();
  el("queue").replaceChildren();
  el("workspace").hidden = true;
  el("connect").hidden = false;
  el("status").textContent = "";
  el("token").focus();
});
el("refresh").addEventListener("click", () => refresh());
el("filter").addEventListener("input", findings);
el("import").addEventListener("click", () => perform("Findings imported.", () => api("import", {})));
