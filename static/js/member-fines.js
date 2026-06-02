/* member-fines.js */

let allFines = [];
let currentTab = 'all';

async function loadFines() {
  try {
    const res = await fetch('/my-fines', { credentials: 'include' });
    const data = await res.json();
    allFines = data.fines || [];
    
    // Update summary cards
    document.getElementById('total-fines').textContent = data.total_fines ?? 0;
    document.getElementById('unpaid-count').textContent = data.unpaid_fines ?? 0;
    document.getElementById('unpaid-amount').textContent = (data.unpaid_amount ?? 0).toFixed(2);
    
    const paidAmount = (data.total_amount ?? 0) - (data.unpaid_amount ?? 0);
    document.getElementById('total-paid').textContent = paidAmount.toFixed(2);
    
    renderFines();
  } catch (err) {
    console.error('Error loading fines:', err);
  }
}

function switchTab(tab) {
  currentTab = tab;
  document.getElementById('tab-all').classList.remove('active');
  document.getElementById('tab-unpaid').classList.remove('active');
  document.getElementById('tab-paid').classList.remove('active');
  document.getElementById(`tab-${tab}`).classList.add('active');
  renderFines();
}

function renderFines() {
  const tbody = document.getElementById('fines-tbody');
  
  let filtered = [];
  if (currentTab === 'all') {
    filtered = allFines;
  } else if (currentTab === 'unpaid') {
    filtered = allFines.filter(f => !f.is_paid);
  } else {
    filtered = allFines.filter(f => f.is_paid);
  }

  if (!filtered.length) {
    tbody.innerHTML = `<tr><td colspan="6" class="loading-row">No ${currentTab} fines</td></tr>`;
    return;
  }

  tbody.innerHTML = filtered.map((f, i) => {
    const statusClass = f.is_paid ? 'badge-success' : 'badge-danger';
    const statusText = f.is_paid ? 'Paid' : 'Unpaid';
    const dueDate = new Date(f.due_date).toLocaleDateString('en-US', { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' });
    const paidOn = f.paid_on ? new Date(f.paid_on).toLocaleDateString('en-US', { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' }) : '—';
    return `
      <tr>
        <td>${i + 1}</td>
        <td>
          <div style="font-weight:600">${f.book_title}</div>
          <div style="color:var(--text-muted);font-size:12px">${f.book_author}</div>
        </td>
        <td>${dueDate}</td>
        <td style="color:var(--danger);font-weight:600">Rs.${f.amount}</td>
        <td><span class="badge ${statusClass}">${statusText}</span></td>
        <td>${paidOn}</td>
      </tr>
    `;
  }).join('');
}

loadFines();
