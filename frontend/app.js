document.addEventListener("DOMContentLoaded", () => {
  updateNav();

  let selectedFile = null;
  let lastResumeId = null;

  const dropZone = document.getElementById("dropZone");
  const fileInput = document.getElementById("resumeInput");
  const analyzeBtn = document.getElementById("analyzeBtn");
  const resultDiv = document.getElementById("result");
  const loading = document.getElementById("loading");
  const jobDescEl = document.getElementById("jobDesc");

  const escapeHtml = value => String(value ?? "").replace(/[&<>'"]/g, ch => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"
  }[ch]));

  dropZone.onclick = () => fileInput.click();
  dropZone.addEventListener("keydown", e => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      fileInput.click();
    }
  });
  fileInput.onchange = () => { if (fileInput.files[0]) setFile(fileInput.files[0]); };

  dropZone.ondragover = e => { e.preventDefault(); dropZone.classList.add("dragover"); };
  dropZone.ondragleave = () => dropZone.classList.remove("dragover");
  dropZone.ondrop = e => {
    e.preventDefault();
    dropZone.classList.remove("dragover");
    if (e.dataTransfer.files[0]) setFile(e.dataTransfer.files[0]);
  };

  function setFile(file) {
    const ext = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
    if (![".pdf", ".doc", ".docx"].includes(ext)) {
      showError("Only PDF, DOC, and DOCX files are supported.");
      return;
    }
    selectedFile = file;
    dropZone.innerHTML = `<p>${escapeHtml(file.name)}</p><span>Ready to analyze</span>`;
    resultDiv.innerHTML = "";
    lastResumeId = null;
  }

  analyzeBtn.onclick = async () => {
    if (!selectedFile) {
      showError("Please upload a resume first.");
      return;
    }

    loading.style.display = "block";
    resultDiv.innerHTML = "";
    analyzeBtn.disabled = true;

    const formData = new FormData();
    formData.append("resume", selectedFile);
    formData.append("job_description", jobDescEl ? jobDescEl.value.trim() : "");

    const headers = {};
    if (isLoggedIn()) headers["Authorization"] = `Bearer ${getToken()}`;

    try {
      const res = await fetch(`${API}/api/analyze`, { method: "POST", headers, body: formData });
      let data;
      try { data = await res.json(); }
      catch { throw new Error(`Server returned ${res.status} with no JSON.`); }

      if (!res.ok || data.error) {
        showError(data.error || `Error ${res.status}`);
        return;
      }

      lastResumeId = data.resume_id;
      sessionStorage.setItem("lastAnalysis", JSON.stringify(data));
      renderResult(data);
    } catch (err) {
      showError(err.message || "Could not connect to server.");
    } finally {
      loading.style.display = "none";
      analyzeBtn.disabled = false;
    }
  };

  function renderResult(data) {
    const score = Number(data.score ?? 0);
    const rank = data.rank ?? "--";
    const keywords = data.keywords ?? [];
    const missing = data.missing ?? [];
    const recs = data.recommendations ?? [];
    const jobs = data.job_suggestions ?? [];
    const jd = data.job_description || "";
    const scoreColor = score >= 70 ? "#22c55e" : score >= 50 ? "#f59e0b" : "#ef4444";

    resultDiv.innerHTML = `
      <div class="result-block" style="text-align:center;">
        <div class="score-ring" style="border-color:${scoreColor};">
          <strong style="color:${scoreColor};">${score}</strong>
          <span>/ 100</span>
        </div>
        <div style="font-size:1.35rem;font-weight:900;margin-bottom:0.5rem;">${escapeHtml(rank)}</div>
        <div class="progress-bar"><div class="progress-fill" style="width:${Math.min(score, 100)}%;background:linear-gradient(90deg,#4f46e5,${scoreColor});"></div></div>
        ${jd ? `<div class="notice" style="display:block;margin-top:0.9rem;">Scored against your pasted job description.</div>` : ""}
      </div>

      ${jobs.length ? `
        <div class="result-block">
          <p class="section-title">Initial job suggestions</p>
          <div style="display:flex;flex-direction:column;gap:0.55rem;">
            ${jobs.slice(0, 3).map((j, i) => `
              <div class="job-suggestion" style="border-color:${i === 0 ? "rgba(34,197,94,0.7)" : "var(--line)"};">
                <div style="display:flex;justify-content:space-between;gap:0.75rem;align-items:center;">
                  <span style="font-weight:800;">${escapeHtml(j.title)}</span>
                  <span style="font-size:0.82rem;color:${i === 0 ? "#22c55e" : "#94a3b8"};">${escapeHtml(j.match)}% match</span>
                </div>
                <div class="progress-bar" style="height:6px;margin-bottom:0;"><div class="progress-fill" style="width:${Number(j.match) || 0}%;background:linear-gradient(90deg,#4f46e5,#14b8a6);"></div></div>
              </div>
            `).join("")}
          </div>
        </div>
      ` : ""}

      ${keywords.length ? `
        <div class="result-block">
          <p class="section-title">Matched keywords</p>
          <div class="chip-list">${keywords.map(k => `<span class="chip good">${escapeHtml(k)}</span>`).join("")}</div>
        </div>
      ` : ""}

      ${missing.length ? `
        <div class="result-block">
          <p class="section-title">Missing keywords</p>
          <div class="chip-list">${missing.map(k => `<span class="chip bad">${escapeHtml(k)}</span>`).join("")}</div>
        </div>
      ` : ""}

      ${recs.length ? `
        <div class="result-block">
          <p class="section-title">Recommendations</p>
          <ul>${recs.map(r => `<li>${escapeHtml(r)}</li>`).join("")}</ul>
        </div>
      ` : ""}

      <div class="btn-row" style="margin-top:1.25rem;">
        <button type="button" onclick="window.location.href='interview.html'">Take Interview</button>
        ${lastResumeId ? `<button type="button" onclick="downloadReport()" style="background:linear-gradient(135deg,#0f766e,#14b8a6);">PDF Report</button>` : ""}
      </div>
    `;
  }

  window.downloadReport = async () => {
    if (!lastResumeId) return;
    const token = getToken();
    const url = `${API}/api/report/${lastResumeId}${token ? "?token=" + token : ""}`;
    try {
      const res = await fetch(url);
      if (!res.ok) { showError("Could not generate PDF."); return; }
      const blob = await res.blob();
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = `resume_report_${lastResumeId}.pdf`;
      link.click();
    } catch (e) {
      showError("PDF download failed: " + e.message);
    }
  };

  function showError(msg) {
    loading.style.display = "none";
    resultDiv.innerHTML = `<div class="err-msg" style="display:block;margin-top:1rem;">${escapeHtml(msg)}</div>`;
  }
});
