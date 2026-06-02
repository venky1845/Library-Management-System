/* members.js */

const BASE = 'http://127.0.0.1:5000';
let allMembers = [];
let deactivateTargetId = null;

// ---- LOAD ----
async function loadMembers() {
  const res = await fetch(`${BASE}/members`, { credentials: 'include' });
  allMembers = await res.json();
  renderMembers(allMembers);
}

function renderMembers(members) {
  const tbody = document.getElementById('members-tbody');
  if (!members.length) {
    tbody.innerHTML = `<tr><td colspan="7" class="loading-row">No members found</td></tr>`;
    return;
  }
  tbody.innerHTML = members.map((m, i) => `
    <tr>
      <td>${i + 1}</td>
      <td><strong>${m.full_name}</strong></td>
      <td>${m.email}</td>
      <td>${m.phone || '—'}</td>
      <td><span class="badge badge-info">${m.active_borrow_count}</span></td>
      <td>
        <span class="badge ${m.is_active ? 'badge-success' : 'badge-danger'}">
          ${m.is_active ? 'Active' : 'Inactive'}
        </span>
      </td>
      <td>
        <button class="btn-icon btn-icon-edit" onclick="viewHistory(${m.id})" title="View History">
          <i class="fa-solid fa-clock-rotate-left"></i>
        </button>
        ${m.is_active
          ? `<button class="btn-icon btn-icon-delete" onclick="openDeactivateModal(${m.id}, '${m.full_name.replace(/'/g,"\\'")}')"><i class="fa-solid fa-ban"></i></button>`
          : `<button class="btn-icon" style="background:rgba(34,197,94,0.15);color:var(--success)" onclick="reactivateMember(${m.id})"><i class="fa-solid fa-check"></i></button>`
        }
      </td>
    </tr>
  `).join('');
}

// ---- SEARCH ----
function filterMembers() {
  const q = document.getElementById('search-input').value.trim().toLowerCase();
  if (!q) { renderMembers(allMembers); return; }
  renderMembers(allMembers.filter(m =>
    m.full_name.toLowerCase().includes(q) || m.email.toLowerCase().includes(q)
  ));
}

// ---- ADD MEMBER MODAL ----
function openAddModal() {
  document.getElementById('form-error').textContent = '';
  document.getElementById('member-name').value   = '';
  document.getElementById('member-email').value  = '';
  document.getElementById('member-phone').value  = '';
  document.getElementById('member-userid').value = '';
  document.getElementById('member-modal').classList.add('open');
}
function closeModal() {
  document.getElementById('member-modal').classList.remove('open');
}

async function saveMember() {
  const full_name = document.getElementById('member-name').value.trim();
  const email     = document.getElementById('member-email').value.trim();
  const phone     = document.getElementById('member-phone').value.trim();
  const user_id   = document.getElementById('member-userid').value.trim();
  const errEl     = document.getElementById('form-error');

  if (!full_name || !email) { errEl.textContent = 'Name and email are required'; return; }

  const res  = await fetch(`${BASE}/members`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ full_name, email, phone, user_id: user_id || null })
  });
  const data = await res.json();
  if (!res.ok) { errEl.textContent = data.message; return; }
  closeModal();
  showToast(data.message);
  loadMembers();
}

// ---- DEACTIVATE ----
function openDeactivateModal(id, name) {
  deactivateTargetId = id;
  document.getElementById('deactivate-member-name').textContent = name;
  document.getElementById('deactivate-modal').classList.add('open');
}
function closeDeactivateModal() {
  document.getElementById('deactivate-modal').classList.remove('open');
}
async function confirmDeactivate() {
  const res  = await fetch(`${BASE}/members/${deactivateTargetId}`, { method: 'DELETE', credentials: 'include' });
  const data = await res.json();
  closeDeactivateModal();
  if (res.ok) { showToast(data.message); loadMembers(); }
  else showToast(data.message, 'error');
}

// ---- REACTIVATE ----
async function reactivateMember(id) {
  const res  = await fetch(`${BASE}/members/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ is_active: true })
  });
  const data = await res.json();
  if (res.ok) { showToast('Member reactivated'); loadMembers(); }
  else showToast(data.message, 'error');
}

// ---- HISTORY MODAL ----
async function viewHistory(member_id) {
  document.getElementById('history-modal').classList.add('open');
  document.getElementById('history-tbody').innerHTML =
    `<tr><td colspan="6" class="loading-row">Loading...</td></tr>`;

  const res  = await fetch(`${BASE}/members/${member_id}/history`, { credentials: 'include' });
  const data = await res.json();
  const rows = data.history || [];

  document.getElementById('history-title').textContent =
    `Borrow History (${data.total_borrows} records)`;

  if (!rows.length) {
    document.getElementById('history-tbody').innerHTML =
      `<tr><td colspan="6" class="loading-row">No history found</td></tr>`;
    return;
  }
  document.getElementById('history-tbody').innerHTML = rows.map((r, i) => `
    <tr>
      <td>${i + 1}</td>
      <td>${r.book_title}</td>
      <td>${r.borrow_date}</td>
      <td>${r.due_date}</td>
      <td>${r.return_date || '—'}</td>
      <td>
        <span class="badge ${r.status === 'active' ? 'badge-warning' : 'badge-success'}">
          ${r.status}
        </span>
        ${r.fine_amount ? `<span class="badge badge-danger" style="margin-left:4px">₹${r.fine_amount} ${r.fine_paid ? '✓' : 'unpaid'}</span>` : ''}
      </td>
    </tr>
  `).join('');
}
function closeHistoryModal() {
  document.getElementById('history-modal').classList.remove('open');
}

loadMembers();