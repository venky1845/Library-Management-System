async function registerUser() {
  const username = document.getElementById("username").value.trim();
  const email    = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value.trim();
  const role     = document.getElementById("role").value;
  const errEl    = document.getElementById("register-error");

  if (!username || !email) {
    errEl.textContent = "Username and email are required";
    return;
  }
  if (role !== "member" && !password) {
    errEl.textContent = "Password is required";
    return;
  }

  try {
    const res  = await fetch("/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, email, password, role })
    });
    const data = await res.json();

    if (!res.ok) {
      errEl.textContent = data.message;
      return;
    }

    alert("Registration Successful");
    window.location.href = "/";

  } catch (err) {
    errEl.textContent = "Registration failed";
    console.error(err);
  }
}

document.addEventListener("keydown", e => {
  if (e.key === "Enter") registerUser();
});