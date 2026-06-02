/* member-dashboard.js */

async function loadDashboard() {
  try {
    const [profileRes, borrowsRes, finesRes] = await Promise.all([
      fetch('/my-profile', { credentials: 'include' }),
      fetch('/my-borrows', { credentials: 'include' }),
      fetch('/my-fines', { credentials: 'include' })
    ]);

    // Check if requests were successful
    if (!profileRes.ok || !borrowsRes.ok || !finesRes.ok) {
      console.error('API Error:', {
        profile: profileRes.status,
        borrows: borrowsRes.status,
        fines: finesRes.status
      });
      
      if (profileRes.status === 404 || borrowsRes.status === 404 || finesRes.status === 404) {
        document.getElementById('due-soon-tbody').innerHTML = `
          <tr><td colspan="3" class="loading-row" style="color: var(--danger);">
            Member profile not found. Please contact support.
          </td></tr>
        `;
        return;
      }
    }

    const profile = await profileRes.json();
    const borrows = await borrowsRes.json();
    const fines = await finesRes.json();

    // Log for debugging
    console.log('Dashboard Data:', { profile, borrows, fines });

    // Update profile section
    document.getElementById('profile-name').textContent = profile.full_name || '—';
    document.getElementById('profile-email').textContent = profile.email || '—';
    document.getElementById('profile-phone').textContent = profile.phone || '—';
    document.getElementById('profile-joined').textContent = profile.joined_on ? new Date(profile.joined_on).toLocaleDateString() : '—';

    // Update stats
    document.getElementById('active-borrows').textContent = borrows.active_borrows ?? 0;
    document.getElementById('overdue-borrows').textContent = borrows.overdue_borrows ?? 0;
    document.getElementById('unpaid-fines').textContent = fines.unpaid_fines ?? 0;
    document.getElementById('total-fine-amount').textContent = `Rs.${fines.unpaid_amount ?? 0}`;

    // Render due soon (show all active books sorted by due date)
    const activeBorrows = borrows.borrows && Array.isArray(borrows.borrows) ? borrows.borrows.filter(b => b.status === 'active') : [];
    const dueSoon = activeBorrows
      .sort((a, b) => new Date(a.due_date) - new Date(b.due_date))
      .slice(0, 5);

    renderDueSoonTable(dueSoon);

    // Render unpaid fines
    const unpaidFinesList = fines.fines && Array.isArray(fines.fines) ? fines.fines.filter(f => !f.is_paid).slice(0, 5) : [];
    renderUnpaidFinesTable(unpaidFinesList);

  } catch (err) {
    console.error('Dashboard load error:', err);
    document.getElementById('due-soon-tbody').innerHTML = `
      <tr><td colspan="3" class="loading-row" style="color: var(--danger);">
        Error loading dashboard. Check console for details.
      </td></tr>
    `;
  }
}

function renderDueSoonTable(rows) {
  const tbody = document.getElementById('due-soon-tbody');
  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="3" class="loading-row">No active borrows</td></tr>`;
    return;
  }
  tbody.innerHTML = rows.map(b => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const dueDate = new Date(b.due_date);
    dueDate.setHours(0, 0, 0, 0);
    const daysLeft = Math.floor((dueDate - today) / (1000 * 60 * 60 * 24));
    const daysLeftColor = daysLeft <= 2 ? 'color: var(--danger)' : daysLeft <= 5 ? 'color: var(--accent2)' : '';
    const formattedDueDate = new Date(b.due_date).toLocaleDateString('en-US', { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' });
    return `
      <tr>
        <td>
          <div style="font-weight:600">${b.book_title}</div>
          <div style="color:var(--text-muted);font-size:12px">${b.book_author}</div>
        </td>
        <td>${formattedDueDate}</td>
        <td><span style="font-weight:600; ${daysLeftColor}">${daysLeft} days</span></td>
      </tr>
    `;
  }).join('');
}

function renderUnpaidFinesTable(rows) {
  const tbody = document.getElementById('unpaid-fines-tbody');
  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="3" class="loading-row">No unpaid fines</td></tr>`;
    return;
  }
  tbody.innerHTML = rows.map(f => `
    <tr>
      <td>
        <div style="font-weight:600">${f.book_title}</div>
        <div style="color:var(--text-muted);font-size:12px">${f.book_author}</div>
      </td>
      <td style="color:var(--danger);font-weight:600">Rs.${f.amount}</td>
      <td>${f.return_date || '—'}</td>
    </tr>
  `).join('');
}

loadDashboard();
