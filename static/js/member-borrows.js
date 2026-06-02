/* member-borrows.js */

let allBorrows = [];
let currentTab = 'active';

async function loadBorrows() {
  try {
    const res = await fetch('/my-borrows', { credentials: 'include' });
    const data = await res.json();
    allBorrows = data.borrows || [];
    renderBorrows();
  } catch (err) {
    console.error('Error loading borrows:', err);
  }
}

function switchTab(tab) {
  currentTab = tab;
  document.getElementById('tab-active').classList.remove('active');
  document.getElementById('tab-history').classList.remove('active');
  document.getElementById(`tab-${tab}`).classList.add('active');
  renderBorrows();
}

function renderBorrows() {
  const tbody = document.getElementById('borrows-tbody');
  
  let filtered = [];
  if (currentTab === 'active') {
    filtered = allBorrows.filter(b => b.status === 'active');
  } else {
    filtered = allBorrows.filter(b => b.status === 'returned');
  }

  if (!filtered.length) {
    tbody.innerHTML = `<tr><td colspan="7" class="loading-row">No ${currentTab} borrows</td></tr>`;
    return;
  }

  tbody.innerHTML = filtered.map((b, i) => {
    const statusClass = b.status === 'active' ? 'badge-success' : 'badge-info';
    const statusText = b.status === 'active' ? 'Active' : 'Returned';
    const overdueClass = b.days_overdue > 0 ? 'color: var(--danger); font-weight: 600;' : '';
    const overdueText = b.days_overdue > 0 ? `${b.days_overdue} days` : 'On Time';
    
    // Format dates properly (remove time portion)
    const borrowDate = new Date(b.borrow_date).toLocaleDateString('en-US', { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' });
    const dueDate = new Date(b.due_date).toLocaleDateString('en-US', { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' });
    const returnDate = b.return_date ? new Date(b.return_date).toLocaleDateString('en-US', { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' }) : '—';
    
    return `
      <tr>
        <td>${i + 1}</td>
        <td><strong>${b.book_title}</strong></td>
        <td>${b.book_author}</td>
        <td>${borrowDate}</td>
        <td>${dueDate}</td>
        <td><span class="badge ${statusClass}">${statusText}</span></td>
        <td><span style="${overdueClass}">${overdueText}</span></td>
      </tr>
    `;
  }).join('');
}

loadBorrows();
