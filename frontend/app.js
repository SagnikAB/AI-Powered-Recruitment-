const API = "https://ai-powered-recruitment-production.up.railway.app";

const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("fileInput");
const resultBox = document.getElementById("result");

let selectedFile = null;

// CLICK
dropZone.addEventListener("click", () => fileInput.click());

// SELECT
fileInput.addEventListener("change", () => {
  selectedFile = fileInput.files[0];
  dropZone.innerHTML = `✅ ${selectedFile.name}`;
});

// DRAG
dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
});

dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  selectedFile = e.dataTransfer.files[0];
  dropZone.innerHTML = `✅ ${selectedFile.name}`;
});

// ANALYZE
async function analyzeResume() {
  if (!selectedFile) {
    alert("Upload file first");
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

    console.log("RAW RESPONSE:", res);

    const data = await res.json();

    console.log("JSON:", data);

    // 🔥 SAFE ACCESS
    if (!data.score) {
      resultBox.innerHTML = "❌ API not returning score";
      return;
    }

    resultBox.innerHTML = `
      <h2>Score: ${data.score}%</h2>
      <p>${data.rank}</p>
    `;
  } catch (err) {
    console.error(err);
    resultBox.innerHTML = "❌ Server error";
  }
}