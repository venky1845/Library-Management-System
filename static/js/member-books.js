/* member-books.js */

let allBooks = [];
let selectedBookId = null;

// ---- LOAD ----
async function loadBooks() {
  const res = await fetch('/books', { credentials: 'include' });
  allBooks = await res.json();
  renderBooks(allBooks);
}

function renderBooks(books) {
  const tbody = document.getElementById('books-tbody');
  if (!books.length) {
    tbody.innerHTML = `<tr><td colspan="7" class="loading-row">No books found</td></tr>`;
    return;
  }
  tbody.innerHTML = books.map((b, i) => `
    <tr>
      <td>${i + 1}</td>
      <td><strong>${b.title}</strong></td>
      <td>${b.author}</td>
      <td>${b.genre || '—'}</td>
      <td style="font-size:12px;color:var(--text-muted)">${b.isbn || '—'}</td>
      <td>
        <span class="badge ${b.available_copies > 0 ? 'badge-success' : 'badge-danger'}">
          ${b.available_copies}
        </span>
      </td>
      <td>
        <button class="btn-icon btn-icon-edit" onclick="openDetailsModal(${b.id})" title="View Details">
          <i class="fa-solid fa-eye"></i>
        </button>
      </td>
    </tr>
  `).join('');
}

// ---- SEARCH ----
async function searchBooks() {
  const q = document.getElementById('search-input').value.trim();
  if (!q) { renderBooks(allBooks); return; }
  const res  = await fetch(`/books/search?q=${encodeURIComponent(q)}`, { credentials: 'include' });
  const data = await res.json();
  renderBooks(Array.isArray(data) ? data : []);
}

// ---- VIEW DETAILS MODAL ----
function openDetailsModal(id) {
  const book = allBooks.find(b => b.id === id);
  if (!book) return;
  
  selectedBookId = id;
  
  document.getElementById('detail-title').textContent = book.title;
  document.getElementById('detail-title-text').textContent = book.title;
  document.getElementById('detail-author').textContent = book.author;
  document.getElementById('detail-genre').textContent = book.genre || '—';
  document.getElementById('detail-isbn').textContent = book.isbn || '—';
  document.getElementById('detail-total').textContent = book.total_copies;
  document.getElementById('detail-available').textContent = book.available_copies;
  
  // Show/hide borrow button based on availability
  const borrowBtn = document.getElementById('borrow-btn');
  if (book.available_copies > 0) {
    borrowBtn.style.display = 'block';
    borrowBtn.disabled = false;
    borrowBtn.textContent = '⊕ Borrow Book';
  } else {
    borrowBtn.style.display = 'block';
    borrowBtn.disabled = true;
    borrowBtn.textContent = '⊖ Not Available';
  }
  
  document.getElementById('book-details-modal').classList.add('open');
}

function closeDetailsModal() {
  document.getElementById('book-details-modal').classList.remove('open');
}

// ---- BORROW BOOK ----
async function borrowBook() {
  if (!selectedBookId) {
    alert('Error: No book selected');
    return;
  }
  
  try {
    const res = await fetch('/member-borrow', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ book_id: selectedBookId })
    });
    
    const data = await res.json();
    
    if (!res.ok) {
      alert(`Error: ${data.message || 'Failed to borrow book'}`);
      return;
    }
    
    alert(`✓ Book borrowed successfully!\nDue Date: ${data.due_date}`);
    closeDetailsModal();
    loadBooks(); // Reload to update availability
    
  } catch (err) {
    console.error('Borrow error:', err);
    alert('Error borrowing book. Please try again.');
  }
}

loadBooks();
