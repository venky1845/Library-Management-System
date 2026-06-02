from flask import Blueprint, request, jsonify
from config import get_db
from routes.auth import login_required, role_required

books_bp = Blueprint("books", __name__)

# ---------------------------------------------------------------------------
# GET /books — View all books
# ---------------------------------------------------------------------------

@books_bp.route("/books", methods=["GET"])
@login_required
def get_books():
    conn, cursor = get_db()
    try:
        cursor.execute("SELECT * FROM books")
        books = cursor.fetchall()
        return jsonify(books), 200
    finally:
        cursor.close()
        conn.close()


# ---------------------------------------------------------------------------
# GET /books/<id> — View a single book
# ---------------------------------------------------------------------------

@books_bp.route("/books/<int:book_id>", methods=["GET"])
@login_required
def get_book(book_id):
    conn, cursor = get_db()
    try:
        cursor.execute("SELECT * FROM books WHERE id=%s", (book_id,))
        book = cursor.fetchone()
        if not book:
            return jsonify({"message": "Book not found"}), 404
        return jsonify(book), 200
    finally:
        cursor.close()
        conn.close()


# ---------------------------------------------------------------------------
# GET /books/search?q= — Search books by title, author, or genre
# ---------------------------------------------------------------------------

@books_bp.route("/books/search", methods=["GET"])
@login_required
def search_books():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"message": "Search query is required"}), 400

    conn, cursor = get_db()
    try:
        like_query = f"%{query}%"
        cursor.execute(
            """
            SELECT * FROM books
            WHERE title LIKE %s
               OR author LIKE %s
               OR genre LIKE %s
            """,
            (like_query, like_query, like_query)
        )
        books = cursor.fetchall()
        return jsonify(books), 200
    finally:
        cursor.close()
        conn.close()


# ---------------------------------------------------------------------------
# POST /books — Add a new book (admin & librarian only)
# ---------------------------------------------------------------------------

@books_bp.route("/books", methods=["POST"])
@login_required
@role_required("admin", "librarian")
def add_book():
    data = request.get_json()

    title           = data.get("title", "").strip()
    author          = data.get("author", "").strip()
    genre           = data.get("genre", "").strip()
    isbn            = data.get("isbn", "").strip()
    total_copies    = data.get("total_copies", 1)
    available_copies = data.get("available_copies", total_copies)

    if not title or not author:
        return jsonify({"message": "Title and author are required"}), 400

    if total_copies < 1:
        return jsonify({"message": "Total copies must be at least 1"}), 400

    conn, cursor = get_db()
    try:
        # Check duplicate ISBN
        if isbn:
            cursor.execute("SELECT id FROM books WHERE isbn=%s", (isbn,))
            if cursor.fetchone():
                return jsonify({"message": "Book with this ISBN already exists"}), 400

        cursor.execute(
            """
            INSERT INTO books (title, author, genre, isbn, total_copies, available_copies)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (title, author, genre or None, isbn or None, total_copies, available_copies)
        )
        conn.commit()
        return jsonify({"message": "Book added successfully"}), 201
    finally:
        cursor.close()
        conn.close()


# ---------------------------------------------------------------------------
# PUT /books/<id> — Edit a book (admin & librarian only)
# ---------------------------------------------------------------------------

@books_bp.route("/books/<int:book_id>", methods=["PUT"])
@login_required
@role_required("admin", "librarian")
def update_book(book_id):
    data = request.get_json()

    conn, cursor = get_db()
    try:
        cursor.execute("SELECT * FROM books WHERE id=%s", (book_id,))
        book = cursor.fetchone()
        if not book:
            return jsonify({"message": "Book not found"}), 404

        title            = data.get("title", book["title"]).strip()
        author           = data.get("author", book["author"]).strip()
        genre            = data.get("genre", book["genre"])
        isbn             = data.get("isbn", book["isbn"])
        total_copies     = data.get("total_copies", book["total_copies"])
        available_copies = data.get("available_copies", book["available_copies"])

        if not title or not author:
            return jsonify({"message": "Title and author are required"}), 400

        if total_copies < 1:
            return jsonify({"message": "Total copies must be at least 1"}), 400

        if available_copies > total_copies:
            return jsonify({"message": "Available copies cannot exceed total copies"}), 400

        cursor.execute(
            """
            UPDATE books
            SET title=%s, author=%s, genre=%s, isbn=%s,
                total_copies=%s, available_copies=%s
            WHERE id=%s
            """,
            (title, author, genre, isbn, total_copies, available_copies, book_id)
        )
        conn.commit()
        return jsonify({"message": "Book updated successfully"}), 200
    finally:
        cursor.close()
        conn.close()


# ---------------------------------------------------------------------------
# DELETE /books/<id> — Delete a book (admin only)
# ---------------------------------------------------------------------------

@books_bp.route("/books/<int:book_id>", methods=["DELETE"])
@login_required
@role_required("admin")
def delete_book(book_id):
    conn, cursor = get_db()
    try:
        cursor.execute("SELECT id FROM books WHERE id=%s", (book_id,))
        if not cursor.fetchone():
            return jsonify({"message": "Book not found"}), 404

        cursor.execute("DELETE FROM books WHERE id=%s", (book_id,))
        conn.commit()
        return jsonify({"message": "Book deleted successfully"}), 200
    finally:
        cursor.close()
        conn.close()