document.addEventListener("DOMContentLoaded", () => {

  let selectedFile = null;

  const dropZone = document.getElementById("dropZone");
  const fileInput = document.getElementById("fileInput");
  const resultDiv = document.getElementById("result");
  const loading = document.getElementById("loading");

  // Safety check
  if (!dropZone || !fileInput) {
    console.error("Elements not found");
    return;
  }

  // Click upload
  dropZone.onclick = () => fileInput.click();

  // File select
  fileInput.onchange = () => {
    selectedFile = fileInput.files[0];
    dropZone.innerHTML = `<p>✅ ${selectedFile.name}</p>`;
  };

  // Drag over
  dropZone.ondragover = (e) => {
    e.preventDefault();
    dropZone.classList.add("dragover");
  };

  // Drag leave
  dropZone.ondragleave = () => {
    dropZone.classList.remove("dragover");
  };

  // Drop
  dropZone.ondrop = (e) => {
    e.preventDefault();
    selectedFile = e.dataTransfer.files[0];
    dropZone.innerHTML = `<p>✅ ${selectedFile.name}</p>`;
  };

  // ================= ANALYZE =================
  window.analyzeResume = async function () {

    if (!selectedFile) {
      alert("Upload a resume first!");
      return;
    }

    loading.style.display = "block";
    resultDiv.innerHTML = "";

    const formData = new FormData();
    formData.append("resume", selectedFile);

    try {
      const res = await fetch(
        "https://ai-powered-recruitment-production.up.railway.app/api/analyze",
        {
          method: "POST",
          body: formData
        }
      );

      const data = await res.json();

      loading.style.display = "none";

      if (data.error) {
        resultDiv.innerHTML = `❌ ${data.error}`;
        return;
      }

      resultDiv.innerHTML = `
        <div class="score-circle">Score: ${data.score}%</div>
        <div class="rank">${data.rank}</div>
      `;

    } catch (err) {
      console.error(err);
      loading.style.display = "none";
      resultDiv.innerHTML = "❌ Server error";
    }
  };

});