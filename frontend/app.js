const API = "https://ai-powered-recruitment-production.up.railway.app";

const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("fileInput");
const resultBox = document.getElementById("result");

let selectedFile = null;

// ================= FILE SELECT =================
dropZone.addEventListener("click", () => fileInput.click());

fileInput.addEventListener("change", () => {
  selectedFile = fileInput.files[0];
  showFile();
});

// ================= DRAG DROP =================
dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropZone.classList.add("dragover");
});

dropZone.addEventListener("dragleave", () => {
  dropZone.classList.remove("dragover");
});

dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  selectedFile = e.dataTransfer.files[0];
  dropZone.classList.remove("dragover");
  showFile();
});

// ================= SHOW FILE =================
function showFile() {
  dropZone.innerHTML = `✅ ${selectedFile.name}`;
}

// ================= ANALYZE =================
async function analyzeResume() {
  if (!selectedFile) {
    alert("Please upload a resume");
    return;
  }

  const formData = new FormData();
  formData.append("resume", selectedFile);

  resultBox.innerHTML = "⏳ Analyzing...";

  try {
    const res = await fetch(API + "/api/analyze", {
      method: "POST",
      body: formData
    });

    const data = await res.json();

    console.log("API RESPONSE:", data); // 🔥 DEBUG

    // ✅ FIXED HERE
    const score = data.score;
    const rank = data.rank;
    const recs = data.recommendations || [];

    resultBox.innerHTML = `
      <div class="score-circle">${score}%</div>
      <div class="rank">${rank}</div>

      <div class="progress-bar">
        <div class="progress-fill" style="width:${score}%"></div>
      </div>

      <h3>Recommendations</h3>
      <ul class="rec-list">
        ${recs.map(r => `<li>${r}</li>`).join("")}
      </ul>
    `;
  } catch (err) {
    console.error(err);
    resultBox.innerHTML = "❌ Error analyzing resume";
  }
}