/* login.js */

async function login() {
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value.trim();
  const errEl = document.getElementById("login-error");

  if (!email || !password) {
    errEl.textContent = "Email and password are required";
    return;
  }

  const res = await fetch("/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json();

  if (!res.ok) {
    errEl.textContent = data.message;
    return;
  }

  if (data.role === "member") {
    window.location.href = "/member-dashboard";
  } else {
    window.location.href = "/dashboard";
  }
}

document.addEventListener("keydown", (e) => {
  if (e.key === "Enter") login();
});
