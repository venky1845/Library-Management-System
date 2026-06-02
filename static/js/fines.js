/* fines.js */

const BASE = 'http://127.0.0.1:5000';
let currentFilter = 'all';

async function loadFines() {
  const url = currentFilter === 'unpaid' ? `${BASE}/fines/unpaid` : `${BASE}/fines`;
  const res  = await fetch(url, { credentials: 'include' });
  const data = await res.json();
  renderFines(data.fines || []);
  loadCollected();
}

async function loadCollected() {
  const res  = await fetch(`${BASE}/fines/collected`, { credentials: 'include' });
  const data = await res.json();
  document.getElementById('total-collected').textContent = `₹${data.total_collected || 0}`;
}

function renderFines(fines) {
  const tbody = document.getElementById('fines-tbody');
  if (!fines.length) {
    tbody.innerHTML = `<tr><td colspan="7" class="loading-row">No fines found</td></tr>`;
    return;
  }
  tbody.innerHTML = fines.map((f, i) => `
    <tr>
      <td>${i + 1}</td>
      <td><strong>${f.member_name}</strong><br><span style="color:var(--text-muted);font-size:12px">${f.member_email}</span></td>
      <td>${f.book_title}</td>
      <td style="font-weight:600;color:var(--accent)">₹${f.amount}</td>
      <td>
        <span class="badge ${f.is_paid ? 'badge-success' : 'badge-danger'}">
          ${f.is_paid ? 'Paid' : 'Unpaid'}
        </span>
      </td>
      <td>${f.paid_on || '—'}</td>
      <td>
        ${!f.is_paid
          ? `<button class="btn-icon btn-icon-pay" onclick="payFine(${f.fine_id})" title="Mark as Paid"><i class="fa-solid fa-check"></i></button>`
          : `<span style="color:var(--text-muted);font-size:12px">—</span>`
        }
      </td>
    </tr>
  `).join('');
}

function filterFines(filter) {
  currentFilter = filter;
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById(`tab-${filter}`).classList.add('active');
  loadFines();
}

async function payFine(fine_id) {
  const res  = await fetch(`${BASE}/fines/${fine_id}/pay`, { method: 'POST', credentials: 'include' });
  const data = await res.json();
  if (res.ok) { showToast(data.message); loadFines(); }
  else showToast(data.message, 'error');
}

loadFines();