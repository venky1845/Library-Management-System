from flask import Blueprint, request, jsonify, session
from datetime import date, timedelta
from config import get_db
from routes.auth import login_required, role_required

borrows_bp = Blueprint("borrows", __name__)

# ---------------------------------------------------------------------------
# POST /borrow — Issue a book to a member
# ---------------------------------------------------------------------------

@borrows_bp.route("/borrow", methods=["POST"])
@login_required
@role_required("admin", "librarian")
def borrow_book():
    data      = request.get_json()
    member_id = data.get("member_id")
    book_id   = data.get("book_id")

    if not member_id or not book_id:
        return jsonify({"message": "member_id and book_id are required"}), 400

    conn, cursor = get_db()
    try:
        # --- Check member exists and is active ---
        cursor.execute("SELECT * FROM members WHERE id=%s", (member_id,))
        member = cursor.fetchone()
        if not member:
            return jsonify({"message": "Member not found"}), 404
        if not member["is_active"]:
            return jsonify({"message": "Member account is deactivated"}), 403

        # --- Check unpaid fines ---
        cursor.execute(
            "SELECT id FROM fines WHERE member_id=%s AND is_paid=FALSE",
            (member_id,)
        )
        if cursor.fetchone():
            return jsonify({
                "message": "Member has unpaid fines. Please clear dues before borrowing"
            }), 403

        # --- Check book exists ---
        cursor.execute("SELECT * FROM books WHERE id=%s", (book_id,))
        book = cursor.fetchone()
        if not book:
            return jsonify({"message": "Book not found"}), 404

        # --- Check availability ---
        if book["available_copies"] < 1:
            return jsonify({"message": "No available copies for this book"}), 400

        # --- Check if member already has this book borrowed ---
        cursor.execute(
            """
            SELECT id FROM borrows
            WHERE member_id=%s AND book_id=%s AND status='active'
            """,
            (member_id, book_id)
        )
        if cursor.fetchone():
            return jsonify({"message": "Member already has this book borrowed"}), 400

        # --- Issue the book ---
        borrow_date = date.today()
        due_date    = borrow_date + timedelta(days=14)

        cursor.execute(
            """
            INSERT INTO borrows (member_id, book_id, borrow_date, due_date)
            VALUES (%s, %s, %s, %s)
            """,
            (member_id, book_id, borrow_date, due_date)
        )

        # --- Reduce available copies ---
        cursor.execute(
            "UPDATE books SET available_copies = available_copies - 1 WHERE id=%s",
            (book_id,)
        )

        conn.commit()
        return jsonify({
            "message":     "Book issued successfully",
            "borrow_date": str(borrow_date),
            "due_date":    str(due_date)
        }), 201

    finally:
        cursor.close()
        conn.close()


# ---------------------------------------------------------------------------
# POST /return/<borrow_id> — Return a book & calculate fine if overdue
# ---------------------------------------------------------------------------

@borrows_bp.route("/return/<int:borrow_id>", methods=["POST"])
@login_required
@role_required("admin", "librarian")
def return_book(borrow_id):
    conn, cursor = get_db()
    try:
        # --- Check borrow record ---
        cursor.execute("SELECT * FROM borrows WHERE id=%s", (borrow_id,))
        borrow = cursor.fetchone()
        if not borrow:
            return jsonify({"message": "Borrow record not found"}), 404

        if borrow["status"] == "returned":
            return jsonify({"message": "Book already returned"}), 400

        return_date = date.today()
        due_date    = borrow["due_date"]

        # --- Calculate fine if overdue ---
        fine_amount  = 0
        fine_created = False

        if return_date > due_date:
            overdue_days = (return_date - due_date).days
            fine_amount  = overdue_days * 5  # Rs. 5 per day

            cursor.execute(
                """
                INSERT INTO fines (borrow_id, member_id, amount)
                VALUES (%s, %s, %s)
                """,
                (borrow_id, borrow["member_id"], fine_amount)
            )
            fine_created = True

        # --- Update borrow record ---
        cursor.execute(
            """
            UPDATE borrows
            SET return_date=%s, status='returned'
            WHERE id=%s
            """,
            (return_date, borrow_id)
        )

        # --- Increase available copies ---
        cursor.execute(
            "UPDATE books SET available_copies = available_copies + 1 WHERE id=%s",
            (borrow["book_id"],)
        )

        conn.commit()

        response = {
            "message":     "Book returned successfully",
            "return_date": str(return_date),
            "fine":        fine_amount
        }
        if fine_created:
            response["fine_message"] = f"Rs. {fine_amount} fine created for overdue return"

        return jsonify(response), 200

    finally:
        cursor.close()
        conn.close()


# ---------------------------------------------------------------------------
# GET /borrows/active — All active borrows
# ---------------------------------------------------------------------------

@borrows_bp.route("/borrows/active", methods=["GET"])
@login_required
@role_required("admin", "librarian")
def active_borrows():
    conn, cursor = get_db()
    try:
        cursor.execute(
            """
            SELECT
                b.id                AS borrow_id,
                m.full_name         AS member_name,
                m.email             AS member_email,
                bk.title            AS book_title,
                bk.author           AS book_author,
                b.borrow_date,
                b.due_date
            FROM borrows b
            JOIN members m  ON m.id  = b.member_id
            JOIN books   bk ON bk.id = b.book_id
            WHERE b.status = 'active'
            ORDER BY b.due_date ASC
            """
        )
        borrows = cursor.fetchall()
        return jsonify({
            "total_active": len(borrows),
            "borrows": borrows
        }), 200
    finally:
        cursor.close()
        conn.close()


# ---------------------------------------------------------------------------
# GET /borrows/overdue — All overdue borrows
# ---------------------------------------------------------------------------

@borrows_bp.route("/borrows/overdue", methods=["GET"])
@login_required
@role_required("admin", "librarian")
def overdue_borrows():
    conn, cursor = get_db()
    try:
        today = date.today()
        cursor.execute(
            """
            SELECT
                b.id                        AS borrow_id,
                m.full_name                 AS member_name,
                m.email                     AS member_email,
                bk.title                    AS book_title,
                bk.author                   AS book_author,
                b.borrow_date,
                b.due_date,
                DATEDIFF(%s, b.due_date)    AS days_overdue,
                DATEDIFF(%s, b.due_date)*5  AS fine_if_returned_today
            FROM borrows b
            JOIN members m  ON m.id  = b.member_id
            JOIN books   bk ON bk.id = b.book_id
            WHERE b.status = 'active'
              AND b.due_date < %s
            ORDER BY days_overdue DESC
            """,
            (today, today, today)
        )
        overdue = cursor.fetchall()
        return jsonify({
            "total_overdue":  len(overdue),
            "overdue_borrows": overdue
        }), 200
    finally:
        cursor.close()
        conn.close()


# ---------------------------------------------------------------------------
# POST /member-borrow — Member borrows a book
# ---------------------------------------------------------------------------

@borrows_bp.route("/member-borrow", methods=["POST"])
@login_required
def member_borrow_book():
    """Allow members to borrow books from the browse page"""
    data    = request.get_json()
    book_id = data.get("book_id")

    if not book_id:
        return jsonify({"message": "book_id is required"}), 400

    conn, cursor = get_db()
    try:
        # --- Resolve member_id from session ---
        if "member_id" in session:
            member_id = session["member_id"]
        else:
            cursor.execute("SELECT id FROM members WHERE user_id=%s", (session.get("user_id"),))
            member = cursor.fetchone()
            if not member:
                return jsonify({"message": "Member profile not found"}), 404
            member_id = member["id"]

        # --- Check member is active ---
        cursor.execute("SELECT is_active FROM members WHERE id=%s", (member_id,))
        member = cursor.fetchone()
        if not member["is_active"]:
            return jsonify({"message": "Your account is deactivated. Contact admin."}), 403

        # --- Check unpaid fines ---
        cursor.execute(
            "SELECT COUNT(*) as cnt FROM fines WHERE member_id=%s AND is_paid=FALSE",
            (member_id,)
        )
        unpaid = cursor.fetchone()
        if unpaid["cnt"] > 0:
            return jsonify({
                "message": f"You have {unpaid['cnt']} unpaid fine(s). Please pay before borrowing."
            }), 403

        # --- Check book exists ---
        cursor.execute("SELECT * FROM books WHERE id=%s", (book_id,))
        book = cursor.fetchone()
        if not book:
            return jsonify({"message": "Book not found"}), 404

        # --- Check availability ---
        if book["available_copies"] < 1:
            return jsonify({"message": "Sorry, no copies available for this book"}), 400

        # --- Check if member already has this book borrowed ---
        cursor.execute(
            """
            SELECT id FROM borrows
            WHERE member_id=%s AND book_id=%s AND status='active'
            """,
            (member_id, book_id)
        )
        if cursor.fetchone():
            return jsonify({"message": "You already have this book borrowed"}), 400

        # --- Borrow the book ---
        borrow_date = date.today()
        due_date    = borrow_date + timedelta(days=14)

        cursor.execute(
            """
            INSERT INTO borrows (member_id, book_id, borrow_date, due_date)
            VALUES (%s, %s, %s, %s)
            """,
            (member_id, book_id, borrow_date, due_date)
        )

        # --- Reduce available copies ---
        cursor.execute(
            "UPDATE books SET available_copies = available_copies - 1 WHERE id=%s",
            (book_id,)
        )

        conn.commit()
        return jsonify({
            "message":     "Book borrowed successfully!",
            "borrow_date": str(borrow_date),
            "due_date":    str(due_date),
            "book_title":  book["title"]
        }), 201

    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()