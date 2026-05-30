/* HealthScan AI — Frontend Logic */

"use strict";

let patients = [];
let deleteTargetId = null;
let drawerPatientId = null;
let searchTimer = null;

// ─── Init ──────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  loadPatients();
  // Prevent future dates on DOB field
  document.getElementById("dob").max = new Date().toISOString().split("T")[0];
});

// ─── API helpers ───────────────────────────────────────────────────
async function api(method, path, body) {
  const opts = {
    method,
    headers: { "Content-Type": "application/json" },
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(`/api${path}`, opts);
  const data = await res.json().catch(() => ({}));
  return { ok: res.ok, status: res.status, data };
}

// ─── Load / Render ─────────────────────────────────────────────────
async function loadPatients(search = "") {
  const q = search ? `?search=${encodeURIComponent(search)}` : "";
  const { ok, data } = await api("GET", `/patients${q}`);
  if (!ok) return;
  patients = data;
  renderTable(patients);
  document.getElementById("totalCount").textContent = patients.length;
}

function renderTable(list) {
  const tbody = document.getElementById("patientTableBody");
  if (!list.length) {
    tbody.innerHTML = `<tr class="empty-row"><td colspan="8">
      <span class="empty-msg">No patient records found.</span></td></tr>`;
    return;
  }
  tbody.innerHTML = list.map((p, i) => `
    <tr>
      <td><span style="font-family:var(--mono);color:var(--text-muted);font-size:0.75rem;">${i + 1}</span></td>
      <td>
        <div class="cell-patient">
          <strong>${esc(p.full_name)}</strong>
          <span>${esc(p.email)}</span>
        </div>
      </td>
      <td style="font-family:var(--mono);font-size:0.8rem;color:var(--text-secondary);">
        ${formatDOB(p.date_of_birth)}
      </td>
      <td>${glucoseChip(p.glucose)}</td>
      <td>${haemoglobinChip(p.haemoglobin)}</td>
      <td>${cholesterolChip(p.cholesterol)}</td>
      <td>
        <div class="remarks-cell" title="${esc(p.remarks)}" onclick="openDrawer(${p.id})">
          ${p.remarks ? esc(p.remarks) : '<span style="color:var(--text-muted)">—</span>'}
        </div>
      </td>
      <td>
        <div class="action-btns">
          <button class="btn-icon" title="Edit" onclick="openEditModal(${p.id})">✎</button>
          <button class="btn-icon delete" title="Delete" onclick="openDelete(${p.id})">✕</button>
        </div>
      </td>
    </tr>
  `).join("");
}

// ─── Value colour chips ────────────────────────────────────────────
function glucoseChip(v) {
  const cls = v < 70 ? "val-warning" : v <= 99 ? "val-normal" : v <= 125 ? "val-warning" : "val-danger";
  return `<span class="val-chip ${cls}">${v}</span>`;
}
function haemoglobinChip(v) {
  const cls = v < 12 ? "val-danger" : v <= 17.5 ? "val-normal" : "val-warning";
  return `<span class="val-chip ${cls}">${v}</span>`;
}
function cholesterolChip(v) {
  const cls = v < 200 ? "val-normal" : v < 240 ? "val-warning" : "val-danger";
  return `<span class="val-chip ${cls}">${v}</span>`;
}

// ─── Modal ─────────────────────────────────────────────────────────
function openModal() {
  document.getElementById("patientId").value = "";
  document.getElementById("modalTitle").textContent = "New Patient Record";
  document.getElementById("patientForm").reset();
  document.getElementById("dob").max = new Date().toISOString().split("T")[0];
  hideErrors();
  document.getElementById("modalOverlay").classList.add("open");
}

function openEditModal(id) {
  const p = patients.find(x => x.id === id);
  if (!p) return;
  document.getElementById("patientId").value = p.id;
  document.getElementById("modalTitle").textContent = "Edit Patient Record";
  document.getElementById("fullName").value = p.full_name;
  document.getElementById("dob").value = p.date_of_birth;
  document.getElementById("dob").max = new Date().toISOString().split("T")[0];
  document.getElementById("email").value = p.email;
  document.getElementById("glucose").value = p.glucose;
  document.getElementById("haemoglobin").value = p.haemoglobin;
  document.getElementById("cholesterol").value = p.cholesterol;
  hideErrors();
  document.getElementById("modalOverlay").classList.add("open");
}

function closeModal() {
  document.getElementById("modalOverlay").classList.remove("open");
}
function closeOnOverlay(e) {
  if (e.target === document.getElementById("modalOverlay")) closeModal();
}

// ─── Save (Create / Update) ────────────────────────────────────────
async function savePatient() {
  hideErrors();

  const id = document.getElementById("patientId").value;
  const payload = {
    full_name:     document.getElementById("fullName").value.trim(),
    date_of_birth: document.getElementById("dob").value,
    email:         document.getElementById("email").value.trim(),
    glucose:       document.getElementById("glucose").value,
    haemoglobin:   document.getElementById("haemoglobin").value,
    cholesterol:   document.getElementById("cholesterol").value,
  };

  // Client-side quick checks
  const localErrors = [];
  if (!payload.full_name) localErrors.push("Full name is required.");
  if (!payload.date_of_birth) localErrors.push("Date of birth is required.");
  if (!payload.email) localErrors.push("Email address is required.");
  if (!payload.glucose || isNaN(payload.glucose)) localErrors.push("Glucose must be a number.");
  if (!payload.haemoglobin || isNaN(payload.haemoglobin)) localErrors.push("Haemoglobin must be a number.");
  if (!payload.cholesterol || isNaN(payload.cholesterol)) localErrors.push("Cholesterol must be a number.");

  if (localErrors.length) { showErrors(localErrors); return; }

  setBtnLoading(true);

  const method = id ? "PUT" : "POST";
  const path   = id ? `/patients/${id}` : "/patients";
  const { ok, data } = await api(method, path, payload);

  setBtnLoading(false);

  if (!ok) {
    showErrors(data.errors || [data.error || "Something went wrong."]);
    return;
  }

  closeModal();
  loadPatients(document.getElementById("searchInput").value.trim());
}

function setBtnLoading(loading) {
  document.getElementById("saveBtnText").style.display   = loading ? "none"   : "inline";
  document.getElementById("saveBtnLoader").style.display = loading ? "inline-block" : "none";
  document.getElementById("saveBtn").disabled = loading;
}

// ─── Delete ────────────────────────────────────────────────────────
function openDelete(id) {
  deleteTargetId = id;
  document.getElementById("deleteOverlay").classList.add("open");
}
function closeDelete() {
  deleteTargetId = null;
  document.getElementById("deleteOverlay").classList.remove("open");
}
async function confirmDelete() {
  if (!deleteTargetId) return;
  const { ok } = await api("DELETE", `/patients/${deleteTargetId}`);
  closeDelete();
  if (ok) loadPatients(document.getElementById("searchInput").value.trim());
}

// ─── Remarks Drawer ────────────────────────────────────────────────
function openDrawer(id) {
  const p = patients.find(x => x.id === id);
  if (!p) return;
  drawerPatientId = id;
  document.getElementById("drawerPatient").innerHTML = `
    <h4>${esc(p.full_name)}</h4>
    <p>${esc(p.email)} · Born ${formatDOB(p.date_of_birth)}</p>
  `;
  document.getElementById("remarksBody").textContent =
    p.remarks || "No assessment available. Click Re-analyse to generate one.";
  document.getElementById("drawerOverlay").classList.add("open");
}
function closeDrawer() {
  document.getElementById("drawerOverlay").classList.remove("open");
}
async function reanalyze() {
  if (!drawerPatientId) return;
  document.getElementById("remarksBody").innerHTML =
    '<span class="ai-generating"><span class="spinner"></span> Analysing with AI…</span>';
  const { ok, data } = await api("POST", `/patients/${drawerPatientId}/analyze`);
  if (ok) {
    document.getElementById("remarksBody").textContent = data.remarks;
    // update in local cache
    const p = patients.find(x => x.id === drawerPatientId);
    if (p) p.remarks = data.remarks;
    renderTable(patients);
  } else {
    document.getElementById("remarksBody").textContent = "Failed to analyse. Please try again.";
  }
}

// ─── Search ────────────────────────────────────────────────────────
function debounceSearch() {
  const val = document.getElementById("searchInput").value;
  document.getElementById("searchClear").classList.toggle("visible", val.length > 0);
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => loadPatients(val.trim()), 300);
}
function clearSearch() {
  document.getElementById("searchInput").value = "";
  document.getElementById("searchClear").classList.remove("visible");
  loadPatients();
}

// ─── Error helpers ─────────────────────────────────────────────────
function showErrors(errors) {
  const box = document.getElementById("errorBox");
  box.style.display = "block";
  box.innerHTML = errors.length === 1
    ? `<p>${esc(errors[0])}</p>`
    : `<ul>${errors.map(e => `<li>${esc(e)}</li>`).join("")}</ul>`;
}
function hideErrors() {
  const box = document.getElementById("errorBox");
  box.style.display = "none";
  box.innerHTML = "";
}

// ─── Utilities ─────────────────────────────────────────────────────
function esc(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
function formatDOB(dob) {
  if (!dob) return "—";
  const d = new Date(dob + "T00:00:00");
  return d.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
}
