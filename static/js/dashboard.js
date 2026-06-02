/* dashboard.js */

async function loadStats() {
  try {
    const [booksRes, membersRes, borrowsRes, overdueRes, finesRes] = await Promise.all([
      fetch('/books',           { credentials: 'include' }),
      fetch('/members',         { credentials: 'include' }),
      fetch('/borrows/active',  { credentials: 'include' }),
      fetch('/borrows/overdue', { credentials: 'include' }),
      fetch('/fines/collected', { credentials: 'include' }),
    ]);

    const books   = await booksRes.json();
    const members = await membersRes.json();
    const borrows = await borrowsRes.json();
    const overdue = await overdueRes.json();
    const fines   = await finesRes.json();

    document.getElementById('total-books').textContent     = Array.isArray(books) ? books.length : '—';
    document.getElementById('total-members').textContent   = Array.isArray(members) ? members.length : '—';
    document.getElementById('active-borrows').textContent  = borrows.total_active ?? '—';
    document.getElementById('overdue-books').textContent   = overdue.total_overdue ?? '—';
    document.getElementById('fines-collected').textContent = `Rs.${fines.total_collected ?? 0}`;

    renderOverdueTable(overdue.overdue_borrows || []);
  } catch (err) {
    console.error('Dashboard load error:', err);
  }
}

function renderOverdueTable(rows) {
  const tbody = document.getElementById('overdue-tbody');
  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="6" class="loading-row">No overdue borrows</td></tr>`;
    return;
  }
  tbody.innerHTML = rows.map((r, i) => `
    <tr>
      <td>${i + 1}</td>
      <td>
        <div style="font-weight:600">${r.member_name}</div>
        <div style="color:var(--text-muted);font-size:12px">${r.member_email}</div>
      </td>
      <td>
        <div>${r.book_title}</div>
        <div style="color:var(--text-muted);font-size:12px">${r.book_author}</div>
      </td>
      <td>${r.due_date}</td>
      <td><span class="badge badge-danger">${r.days_overdue} days</span></td>
      <td style="color:var(--danger);font-weight:600">Rs.${r.fine_if_returned_today}</td>
    </tr>
  `).join('');
}

loadStats();