async function uploadResume(file) {
  const resultDiv = document.getElementById("result");
  const loading = document.getElementById("loading");

  loading.style.display = "block";
  resultDiv.innerHTML = "";

  const formData = new FormData();
  formData.append("resume", file);

  try {
    const res = await fetch("https://YOUR-RAILWAY-URL/api/analyze", {
      method: "POST",
      body: formData
    });

    const data = await res.json();
    console.log(data);

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
    loading.style.display = "none";
    resultDiv.innerHTML = "❌ Server error";
  }
}