// ── Shared auth helpers used across all pages ─────────────────────────────
const API = "https://ai-powered-recruitment-production.up.railway.app";

function getToken()    { return localStorage.getItem("token") || ""; }
function getUsername() { return localStorage.getItem("username") || "Guest"; }
function isLoggedIn()  { return !!getToken(); }

function saveSession(token, username) {
  localStorage.setItem("token", token);
  localStorage.setItem("username", username);
}

function clearSession() {
  localStorage.removeItem("token");
  localStorage.removeItem("username");
}

async function logout() {
  await fetch(`${API}/api/auth/logout`, {
    method: "POST",
    headers: { Authorization: `Bearer ${getToken()}` }
  }).catch(() => {});
  clearSession();
  window.location.href = "login.html";
}

// Update navbar to show logged-in state
function updateNav() {
  const navUser = document.getElementById("navUser");
  const navLogin = document.getElementById("navLogin");
  const navLogout = document.getElementById("navLogout");

  if (!navUser) return;

  if (isLoggedIn()) {
    navUser.textContent   = `👤 ${getUsername()}`;
    navUser.style.display = "inline";
    if (navLogin)  navLogin.style.display  = "none";
    if (navLogout) navLogout.style.display = "inline";
  } else {
    navUser.style.display  = "none";
    if (navLogin)  navLogin.style.display  = "inline";
    if (navLogout) navLogout.style.display = "none";
  }
}