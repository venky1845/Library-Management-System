/* login.js */

function switchTab(tab) {
  document.getElementById('tab-staff').classList.toggle('active', tab === 'staff');
  document.getElementById('tab-member').classList.toggle('active', tab === 'member');
  document.getElementById('panel-staff').classList.toggle('active', tab === 'staff');
  document.getElementById('panel-member').classList.toggle('active', tab === 'member');
}

async function staffLogin() {
  const email    = document.getElementById('staff-email').value.trim();
  const password = document.getElementById('staff-password').value.trim();
  const errEl    = document.getElementById('staff-error');

  if (!email || !password) { errEl.textContent = 'Email and password are required'; return; }

  const res  = await fetch('/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ email, password })
  });
  const data = await res.json();

  if (!res.ok) { errEl.textContent = data.message; return; }

  window.location.href = data.role === 'member' ? '/member-dashboard' : '/dashboard';
}

async function memberLogin() {
  const full_name = document.getElementById('member-name').value.trim();
  const email     = document.getElementById('member-email').value.trim();
  const errEl     = document.getElementById('member-error');

  if (!full_name || !email) { errEl.textContent = 'Full name and email are required'; return; }

  const res  = await fetch('/member-login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ full_name, email })
  });
  const data = await res.json();

  if (!res.ok) { errEl.textContent = data.message; return; }

  window.location.href = '/member-dashboard';
}

document.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    document.getElementById('tab-staff').classList.contains('active') ? staffLogin() : memberLogin();
  }
});