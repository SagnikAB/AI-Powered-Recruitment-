const BACKEND_URL = "https://YOUR-RAILWAY-URL/api/analyze"; // 🔥 replace this

async function upload() {
  const file = document.getElementById("fileInput").files[0];

  if (!file) {
    alert("Select a file");
    return;
  }

  const formData = new FormData();
  formData.append("resume", file);

  document.getElementById("result").innerHTML = "Analyzing... ⏳";

  try {
    const res = await fetch(BACKEND_URL, {
      method: "POST",
      body: formData
    });

    const data = await res.json();

    document.getElementById("result").innerHTML = `
      <div class="result-card">
        <h2>Score: ${data.score}%</h2>
        <h3>${data.rank}</h3>

        <h4>Skills</h4>
        ${data.keywords.map(k => `<span class="tag">${k}</span>`).join("")}

        <h4>Missing Skills</h4>
        ${data.missing.map(m => `<span class="tag missing">${m}</span>`).join("")}
      </div>
    `;

  } catch (err) {
    document.getElementById("result").innerHTML = "Error ❌";
  }
}