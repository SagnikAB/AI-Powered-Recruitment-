const API = "https://ai-powered-recruitment-production.up.railway.app";

const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("fileInput");
const resultBox = document.getElementById("result");

let selectedFile = null;

// ================= CLICK TO SELECT =================
dropZone.addEventListener("click", () => {
  fileInput.click();
});

// ================= FILE SELECT =================
fileInput.addEventListener("change", () => {
  if (fileInput.files.length > 0) {
    selectedFile = fileInput.files[0];
    showFile();
  }
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

  if (e.dataTransfer.files.length > 0) {
    selectedFile = e.dataTransfer.files[0];
    showFile();
  }

  dropZone.classList.remove("dragover");
});

// ================= SHOW FILE =================
function showFile() {
  dropZone.innerHTML = `✅ ${selectedFile.name}`;
}

// ================= ANALYZE =================
async function analyzeResume() {
  if (!selectedFile) {
    alert("❌ Please upload a resume first");
    return;
  }

  const formData = new FormData();
  formData.append("resume", selectedFile);

  console.log("Uploading:", selectedFile); // DEBUG

  resultBox.innerHTML = "⏳ Analyzing...";

  try {
    const res = await fetch(API + "/api/analyze", {
      method: "POST",
      body: formData
    });

    const data = await res.json();

    console.log("Response:", data); // DEBUG

    resultBox.innerHTML = `
      <h2>${data.score}%</h2>
      <p>${data.rank}</p>
    `;
  } catch (err) {
    console.error(err);
    resultBox.innerHTML = "❌ Upload failed";
  }
}