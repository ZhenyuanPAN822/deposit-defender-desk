const state = { evidence: [], deductions: [], report: null };
const $ = (id) => document.getElementById(id);
const money = (value) => `$${Number(value || 0).toFixed(2)}`;

async function api(path, payload) {
  const response = await fetch(path, {
    method: payload ? "POST" : "GET",
    headers: payload ? { "Content-Type": "application/json" } : {},
    body: payload ? JSON.stringify(payload) : undefined,
  });
  const data = await response.json();
  if (!response.ok || data.error) throw new Error(data.error || `Request failed ${response.status}`);
  return data;
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[char]));
}
function setStatus(text) { $("status").textContent = text; }

function renderInputs() {
  $("evidenceList").innerHTML = state.evidence.slice(0, 20).map((item) => `<div class="item"><strong>${escapeHtml(item.area)}</strong><p>${escapeHtml(item.description)}</p><span class="pill">${item.stage}</span><span class="pill">${item.date}</span></div>`).join("") || `<p class="muted">No evidence imported.</p>`;
  $("deductionList").innerHTML = state.deductions.map((item) => `<div class="item"><strong>${escapeHtml(item.description)}</strong><p>${money(item.amount)} · ${escapeHtml(item.area)}</p><span class="pill">${item.category}</span></div>`).join("") || `<p class="muted">No deductions imported.</p>`;
}

function renderReport(report) {
  $("mDeductions").textContent = report.summary.deduction_count;
  $("mEvidence").textContent = report.summary.evidence_count;
  $("mTotal").textContent = money(report.summary.total_deductions);
  $("mLate").textContent = report.summary.notice_late ? "yes" : "no";
  $("findings").innerHTML = report.findings.map((row) => {
    const level = row.dispute_strength >= 70 ? "high" : row.dispute_strength >= 40 ? "medium" : "";
    return `<div class="card ${level}">
      <strong>${escapeHtml(row.description)}</strong>
      <span class="pill">${money(row.amount)}</span>
      <span class="pill">score ${row.dispute_strength}</span>
      <span class="pill">${row.recommended_action}</span>
      <p>${row.evidence_checklist.map(escapeHtml).join(" · ")}</p>
    </div>`;
  }).join("");
  $("gaps").innerHTML = report.findings.map((row) => `
    <div class="card">
      <strong>${escapeHtml(row.area)} · ${escapeHtml(row.category)}</strong>
      <p>${row.matched_evidence.evidence_gaps.map(escapeHtml).join(", ") || "No major evidence gaps detected."}</p>
      <p class="muted">Matched evidence: ${row.matched_evidence.same_area_evidence.length}</p>
    </div>
  `).join("");
  $("outline").textContent = `${report.draft_dispute_outline}\n\nSaved outputs:\n${JSON.stringify(report.saved_outputs, null, 2)}`;
}

document.querySelectorAll(".tab").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((item) => item.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    $(`tab-${button.dataset.tab}`).classList.add("active");
  });
});

$("loadSample").addEventListener("click", async () => {
  try {
    const data = await api("/api/sample");
    state.evidence = data.evidence;
    state.deductions = data.deductions;
    renderInputs();
    setStatus(`Loaded ${state.evidence.length} evidence items and ${state.deductions.length} deductions.`);
  } catch (error) { setStatus(error.message); }
});

$("parseEvidence").addEventListener("click", async () => {
  try {
    const data = await api("/api/parse-evidence", { csv: $("evidenceCsv").value });
    state.evidence = data.evidence;
    renderInputs();
    setStatus(`Parsed ${data.metadata.evidence_count} evidence rows.`);
  } catch (error) { setStatus(error.message); }
});

$("parseDeductions").addEventListener("click", async () => {
  try {
    const data = await api("/api/parse-deductions", { csv: $("deductionCsv").value });
    state.deductions = data.deductions;
    renderInputs();
    setStatus(`Parsed ${data.metadata.deduction_count} deduction rows.`);
  } catch (error) { setStatus(error.message); }
});

$("parseNotes").addEventListener("click", async () => {
  try {
    const data = await api("/api/parse-notes", { text: $("noteText").value });
    state.evidence = [...state.evidence, ...data.evidence];
    renderInputs();
    setStatus(`Extracted ${data.metadata.evidence_count} note blocks. Rejected: ${data.metadata.rejected_blocks.length}`);
  } catch (error) { setStatus(error.message); }
});

$("runAnalysis").addEventListener("click", async () => {
  try {
    const report = await api("/api/analyze", {
      evidence: state.evidence,
      deductions: state.deductions,
      rule_json: $("ruleJson").value.trim() || null,
      case: {
        state: $("state").value || "GENERIC",
        move_out_date: $("moveOutDate").value,
        deposit_amount: Number($("depositAmount").value || 0),
        deduction_notice_date: $("noticeDate").value,
        forwarding_address_sent: true,
      },
    });
    state.report = report;
    renderReport(report);
    setStatus("Analysis complete. Reports saved locally in outputs/.");
  } catch (error) { setStatus(error.message); }
});

renderInputs();

