document.addEventListener("DOMContentLoaded", () => {

  updateNav();   // from auth.js

  let selectedFile  = null;
  let lastResumeId  = null;

  const dropZone   = document.getElementById("dropZone");
  const fileInput  = document.getElementById("resumeInput");
  const analyzeBtn = document.getElementById("analyzeBtn");
  const resultDiv  = document.getElementById("result");
  const loading    = document.getElementById("loading");
  const jobDescEl  = document.getElementById("jobDesc");

  // ── File handling ─────────────────────────────────────────────────────────
  dropZone.onclick = () => fileInput.click();

  fileInput.onchange = () => {
    if (fileInput.files[0]) setFile(fileInput.files[0]);
  };

  dropZone.ondragover  = e => { e.preventDefault(); dropZone.classList.add("dragover"); };
  dropZone.ondragleave = () => dropZone.classList.remove("dragover");
  dropZone.ondrop      = e => {
    e.preventDefault();
    dropZone.classList.remove("dragover");
    if (e.dataTransfer.files[0]) setFile(e.dataTransfer.files[0]);
  };

  function setFile(file) {
    const ext = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
    if (![".pdf",".doc",".docx"].includes(ext)) {
      showError("Only PDF, DOC, DOCX files are supported."); return;
    }
    selectedFile = file;
    dropZone.innerHTML = `<p>✅ ${file.name}</p>`;
    resultDiv.innerHTML = "";
    lastResumeId = null;
  }

  // ── Analyze ───────────────────────────────────────────────────────────────
  analyzeBtn.onclick = async () => {
    if (!selectedFile) { alert("Please upload a resume first!"); return; }

    loading.style.display = "block";
    resultDiv.innerHTML   = "";
    analyzeBtn.disabled   = true;

    const formData = new FormData();
    formData.append("resume", selectedFile);
    formData.append("job_description", jobDescEl ? jobDescEl.value.trim() : "");

    const headers = {};
    if (isLoggedIn()) headers["Authorization"] = `Bearer ${getToken()}`;

    try {
      const res = await fetch(`${API}/api/analyze`, {
        method: "POST",
        headers,
        body: formData,
      });

      let data;
      try { data = await res.json(); }
      catch { throw new Error(`Server returned ${res.status} with no JSON body.`); }

      if (!res.ok || data.error) { showError(data.error || `Error ${res.status}`); return; }

      lastResumeId = data.resume_id;
      renderResult(data);

    } catch (err) {
      showError(err.message || "Could not connect to server.");
    } finally {
      loading.style.display = "none";
      analyzeBtn.disabled   = false;
    }
  };

  // ── Render result ─────────────────────────────────────────────────────────
  function renderResult(data) {
    const score    = data.score    ?? 0;
    const rank     = data.rank     ?? "--";
    const keywords = data.keywords ?? [];
    const missing  = data.missing  ?? [];
    const recs     = data.recommendations ?? [];
    const jd       = data.job_description || "";

    const scoreColor = score >= 70 ? "#22c55e" : score >= 50 ? "#f59e0b" : "#ef4444";

    resultDiv.innerHTML = `
      <div style="margin-top:20px;">

        <!-- Score -->
        <div style="
          width:120px;height:120px;border-radius:50%;
          border:4px solid ${scoreColor};
          display:flex;flex-direction:column;
          align-items:center;justify-content:center;
          margin:0 auto 12px;
        ">
          <span style="font-size:32px;font-weight:700;color:${scoreColor}">${score}</span>
          <span style="font-size:11px;color:#9ca3af;">/ 100</span>
        </div>

        <!-- Rank -->
        <div style="font-size:22px;font-weight:600;margin-bottom:8px;">${rank}</div>

        <!-- Progress bar -->
        <div class="progress-bar">
          <div class="progress-fill" style="width:${score}%;background:linear-gradient(90deg,#6366f1,${scoreColor});"></div>
        </div>

        ${jd ? `
          <div style="margin-top:16px;padding:10px 14px;background:rgba(99,102,241,0.08);
            border:1px solid #6366f1;border-radius:10px;text-align:left;">
            <p style="font-size:0.82rem;color:#a5b4fc;font-weight:600;margin-bottom:4px;">🎯 Scored against your job description</p>
          </div>
        ` : ""}

        <!-- Matched keywords -->
        ${keywords.length ? `
          <div style="margin-top:18px;text-align:left;">
            <p style="font-weight:600;margin-bottom:8px;">✅ Matched Keywords</p>
            <div style="display:flex;flex-wrap:wrap;gap:6px;">
              ${keywords.map(k => `
                <span style="background:rgba(34,197,94,0.12);border:1px solid #22c55e;
                  color:#22c55e;border-radius:20px;padding:3px 12px;font-size:13px;">${k}</span>
              `).join("")}
            </div>
          </div>
        ` : ""}

        <!-- Missing keywords -->
        ${missing.length ? `
          <div style="margin-top:14px;text-align:left;">
            <p style="font-weight:600;margin-bottom:8px;">❌ Missing Keywords</p>
            <div style="display:flex;flex-wrap:wrap;gap:6px;">
              ${missing.map(k => `
                <span style="background:rgba(239,68,68,0.1);border:1px solid #ef4444;
                  color:#ef4444;border-radius:20px;padding:3px 12px;font-size:13px;">${k}</span>
              `).join("")}
            </div>
          </div>
        ` : ""}

        <!-- Recommendations -->
        ${recs.length ? `
          <div style="margin-top:14px;text-align:left;">
            <p style="font-weight:600;margin-bottom:8px;">💡 Recommendations</p>
            <ul style="padding-left:18px;color:#d1d5db;font-size:14px;line-height:1.8;">
              ${recs.map(r => `<li>${r}</li>`).join("")}
            </ul>
          </div>
        ` : ""}

        <!-- Download PDF -->
        ${lastResumeId ? `
          <button onclick="downloadReport()" style="margin-top:20px;
            background:linear-gradient(135deg,#059669,#10b981);">
            📥 Download PDF Report
          </button>
        ` : ""}

      </div>
    `;
  }

  // ── PDF download ──────────────────────────────────────────────────────────
  window.downloadReport = async () => {
    if (!lastResumeId) return;

    const token = getToken();
    const url   = `${API}/api/report/${lastResumeId}${token ? "?token=" + token : ""}`;

    const btn = resultDiv.querySelector("button");
    if (btn) { btn.textContent = "⏳ Generating..."; btn.disabled = true; }

    try {
      const res = await fetch(url);
      if (!res.ok) { showError("Could not generate PDF report."); return; }

      const blob = await res.blob();
      const link = document.createElement("a");
      link.href  = URL.createObjectURL(blob);
      link.download = `resume_report_${lastResumeId}.pdf`;
      link.click();
    } catch (e) {
      showError("PDF download failed: " + e.message);
    } finally {
      if (btn) { btn.textContent = "📥 Download PDF Report"; btn.disabled = false; }
    }
  };

  // ── Helpers ───────────────────────────────────────────────────────────────
  function showError(msg) {
    loading.style.display = "none";
    resultDiv.innerHTML = `
      <div style="margin-top:16px;padding:12px 16px;
        background:rgba(239,68,68,0.12);border:1px solid #ef4444;
        border-radius:10px;color:#ef4444;font-size:14px;">❌ ${msg}</div>
    `;
  }

});