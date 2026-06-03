

const BASE = 'http://127.0.0.1:5000';
let currentTab = 'active';

function switchTab(tab) {
  currentTab = tab;
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById(`tab-${tab}`).classList.add('active');
  if (tab === 'active')  loadActive();
  if (tab === 'overdue') loadOverdue();
}


async function loadActive() {
  document.getElementById('borrows-tbody').innerHTML =
    `<tr><td colspan="7" class="loading-row">Loading...</td></tr>`;
  const res  = await fetch(`${BASE}/borrows/active`, { credentials: 'include' });
  const data = await res.json();
  renderActive(data.borrows || []);
}

function renderActive(rows) {
  const tbody = document.getElementById('borrows-tbody');
  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="7" class="loading-row">No active borrows</td></tr>`;
    return;
  }
  tbody.innerHTML = rows.map((r, i) => `
    <tr>
      <td>${i + 1}</td>
      <td><strong>${r.member_name}</strong><br><span style="color:var(--text-muted);font-size:12px">${r.member_email}</span></td>
      <td>${r.book_title}<br><span style="color:var(--text-muted);font-size:12px">${r.book_author}</span></td>
      <td>${r.borrow_date}</td>
      <td>${r.due_date}</td>
      <td><span class="badge badge-warning">Active</span></td>
      <td>
        <button class="btn-icon btn-icon-pay" onclick="confirmReturn(${r.borrow_id}, '${r.book_title.replace(/'/g,"\\'")}', '${r.member_name.replace(/'/g,"\\'")}')">
          <i class="fa-solid fa-rotate-left"></i>
        </button>
      </td>
    </tr>
  `).join('');
}

// ---- OVERDUE BORROWS ----
async function loadOverdue() {
  document.getElementById('borrows-tbody').innerHTML =
    `<tr><td colspan="7" class="loading-row">Loading...</td></tr>`;
  const res  = await fetch(`${BASE}/borrows/overdue`, { credentials: 'include' });
  const data = await res.json();
  renderOverdue(data.overdue_borrows || []);
}

function renderOverdue(rows) {
  const tbody = document.getElementById('borrows-tbody');
  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="7" class="loading-row">No overdue borrows 🎉</td></tr>`;
    return;
  }
  tbody.innerHTML = rows.map((r, i) => `
    <tr>
      <td>${i + 1}</td>
      <td><strong>${r.member_name}</strong><br><span style="color:var(--text-muted);font-size:12px">${r.member_email}</span></td>
      <td>${r.book_title}<br><span style="color:var(--text-muted);font-size:12px">${r.book_author}</span></td>
      <td>${r.borrow_date}</td>
      <td>${r.due_date}</td>
      <td><span class="badge badge-danger">${r.days_overdue} days overdue</span></td>
      <td>
        <span style="color:var(--danger);font-weight:600;font-size:12px">₹${r.fine_if_returned_today}</span>
        <button class="btn-icon btn-icon-pay" style="margin-left:6px" onclick="confirmReturn(${r.borrow_id}, '${r.book_title.replace(/'/g,"\\'")}', '${r.member_name.replace(/'/g,"\\'")}')">
          <i class="fa-solid fa-rotate-left"></i>
        </button>
      </td>
    </tr>
  `).join('');
}

// ---- ISSUE BOOK MODAL ----
async function openIssueModal() {
  document.getElementById('issue-error').textContent = '';
  document.getElementById('issue-member').value = '';
  document.getElementById('issue-book').value   = '';
  document.getElementById('issue-modal').classList.add('open');
}
function closeIssueModal() {
  document.getElementById('issue-modal').classList.remove('open');
}

async function issueBook() {
  const member_id = document.getElementById('issue-member').value.trim();
  const book_id   = document.getElementById('issue-book').value.trim();
  const errEl     = document.getElementById('issue-error');

  if (!member_id || !book_id) { errEl.textContent = 'Both Member ID and Book ID are required'; return; }

  const res  = await fetch(`${BASE}/borrow`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ member_id: parseInt(member_id), book_id: parseInt(book_id) })
  });
  const data = await res.json();
  if (!res.ok) { errEl.textContent = data.message; return; }

  closeIssueModal();
  showToast(`${data.message} — Due: ${data.due_date}`);
  loadActive();
}

// ---- RETURN MODAL ----
let returnTargetId = null;
function confirmReturn(borrow_id, bookTitle, memberName) {
  returnTargetId = borrow_id;
  document.getElementById('return-book-name').textContent   = bookTitle;
  document.getElementById('return-member-name').textContent = memberName;
  document.getElementById('return-modal').classList.add('open');
}
function closeReturnModal() {
  document.getElementById('return-modal').classList.remove('open');
}

async function processReturn() {
  const res  = await fetch(`${BASE}/return/${returnTargetId}`, { method: 'POST', credentials: 'include' });
  const data = await res.json();
  closeReturnModal();
  if (res.ok) {
    const msg = data.fine_message ? `${data.message} — ${data.fine_message}` : data.message;
    showToast(msg);
    switchTab(currentTab);
  } else {
    showToast(data.message, 'error');
  }
}

// Initial load
loadActive();