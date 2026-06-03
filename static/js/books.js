/* books.js */

let allBooks = [];
let deleteTargetId = null;

// ---- LOAD ----
async function loadBooks() {
  const res = await fetch('/books', { credentials: 'include' });
  allBooks = await res.json();
  renderBooks(allBooks);
}

function renderBooks(books) {
  const tbody = document.getElementById('books-tbody');
  if (!books.length) {
    tbody.innerHTML = `<tr><td colspan="8" class="loading-row">No books found</td></tr>`;
    return;
  }
  tbody.innerHTML = books.map((b, i) => `
    <tr>
      <td>${i + 1}</td>
      <td><strong>${b.title}</strong></td>
      <td>${b.author}</td>
      <td>${b.genre || '—'}</td>
      <td style="font-size:12px;color:var(--text-muted)">${b.isbn || '—'}</td>
      <td>${b.total_copies}</td>
      <td>
        <span class="badge ${b.available_copies > 0 ? 'badge-success' : 'badge-danger'}">
          ${b.available_copies}
        </span>
      </td>
      <td>
        <button class="btn-icon btn-icon-edit"   onclick="openEditModal(${b.id})" title="Edit"><i class="fa-solid fa-pen"></i></button>
        <button class="btn-icon btn-icon-delete" onclick="openDeleteModal(${b.id}, '${b.title.replace(/'/g,"\\'")}')"><i class="fa-solid fa-trash"></i></button>
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

// ---- ADD MODAL ----
function openAddModal() {
  document.getElementById('modal-title').textContent    = 'Add Book';
  document.getElementById('book-id').value              = '';
  document.getElementById('book-title').value           = '';
  document.getElementById('book-author').value          = '';
  document.getElementById('book-genre').value           = '';
  document.getElementById('book-isbn').value            = '';
  document.getElementById('book-total').value           = 1;
  document.getElementById('book-available').value       = 1;
  document.getElementById('form-error').textContent     = '';
  document.getElementById('book-modal').classList.add('open');
}

// ---- EDIT MODAL ----
function openEditModal(id) {
  const book = allBooks.find(b => b.id === id);
  if (!book) return;
  document.getElementById('modal-title').textContent    = 'Edit Book';
  document.getElementById('book-id').value              = book.id;
  document.getElementById('book-title').value           = book.title;
  document.getElementById('book-author').value          = book.author;
  document.getElementById('book-genre').value           = book.genre  || '';
  document.getElementById('book-isbn').value            = book.isbn   || '';
  document.getElementById('book-total').value           = book.total_copies;
  document.getElementById('book-available').value       = book.available_copies;
  document.getElementById('form-error').textContent     = '';
  document.getElementById('book-modal').classList.add('open');
}

function closeModal() {
  document.getElementById('book-modal').classList.remove('open');
}

// ---- SAVE ----
async function saveBook() {
  const id        = document.getElementById('book-id').value;
  const title     = document.getElementById('book-title').value.trim();
  const author    = document.getElementById('book-author').value.trim();
  const genre     = document.getElementById('book-genre').value.trim();
  const isbn      = document.getElementById('book-isbn').value.trim();
  const total     = parseInt(document.getElementById('book-total').value);
  const available = parseInt(document.getElementById('book-available').value);
  const errEl     = document.getElementById('form-error');

  if (!title || !author) { errEl.textContent = 'Title and author are required'; return; }
  if (available > total) { errEl.textContent = 'Available cannot exceed total copies'; return; }

  const body   = { title, author, genre, isbn, total_copies: total, available_copies: available };
  const url    = id ? `/books/${id}` : `/books`;
  const method = id ? 'PUT' : 'POST';

  const res  = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(body)
  });
  const data = await res.json();
  if (!res.ok) { errEl.textContent = data.message; return; }
  closeModal();
  showToast(data.message);
  loadBooks();
}

// ---- DELETE ----
function openDeleteModal(id, title) {
  deleteTargetId = id;
  document.getElementById('delete-book-name').textContent = title;
  document.getElementById('delete-modal').classList.add('open');
}
function closeDeleteModal() {
  document.getElementById('delete-modal').classList.remove('open');
}
async function confirmDelete() {
  const res  = await fetch(`/books/${deleteTargetId}`, { method: 'DELETE', credentials: 'include' });
  const data = await res.json();
  closeDeleteModal();
  if (res.ok) { showToast(data.message); loadBooks(); }
  else showToast(data.message, 'error');
}

loadBooks();