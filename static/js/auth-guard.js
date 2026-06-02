/* auth-guard.js — runs on every protected page */

let currentUser = null;

async function checkAuth() {
  try {
    const res = await fetch('/profile', { credentials: 'include' });
    if (!res.ok) {
      window.location.href = '/';
      return null;
    }
    const user = await res.json();
    currentUser = user;
    const el = document.getElementById('username-display');
    if (el) el.textContent = user.username;
    return user;
  } catch {
    window.location.href = '/';
    return null;
  }
}

async function logout() {
  try {
    await fetch('/logout', {
      method: 'POST',
      credentials: 'include'
    });

    window.location.href = '/';
  } catch (err) {
    console.error('Logout failed:', err);
  }
}

function showToast(message, type = 'success') {
  const existing = document.querySelector('.toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

function isAdmin() {
  return currentUser && currentUser.role === 'admin';
}

function isLibrarian() {
  return currentUser && currentUser.role === 'librarian';
}

function isMember() {
  return currentUser && currentUser.role === 'member';
}

function checkRole(allowedRoles) {
  if (!currentUser) return false;
  return allowedRoles.includes(currentUser.role);
}

checkAuth();