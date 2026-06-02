from flask import Blueprint, request, jsonify, session
from datetime import date, timedelta
from config import get_db
from routes.auth import login_required, role_required

borrows_bp = Blueprint("borrows", __name__)

# ------------------------------------------------------------------
# Borrow Book
# ------------------------------------------------------------------

@borrows_bp.route("/borrow", methods=["POST"])
@login_required
@role_required("admin", "librarian")
def borrow_book():

    data = request.get_json()

    member_id = data.get("member_id")
    book_id = data.get("book_id")

    if not member_id or not book_id:
        return jsonify({
            "message": "member_id and book_id are required"
        }), 400

    conn, cursor = get_db()

    try:

        # Check member
        cursor.execute(
            "SELECT * FROM members WHERE id=%s",
            (member_id,)
        )
        member = cursor.fetchone()

        if not member:
            return jsonify({
                "message": "Member not found"
            }), 404

        if not member["is_active"]:
            return jsonify({
                "message": "Member is inactive"
            }), 403

        # Check unpaid fines
        cursor.execute(
            """
            SELECT *
            FROM fines
            WHERE member_id=%s
            AND is_paid=FALSE
            """,
            (member_id,)
        )

        if cursor.fetchone():
            return jsonify({
                "message": "Member has unpaid fines"
            }), 400

        # Check book
        cursor.execute(
            "SELECT * FROM books WHERE id=%s",
            (book_id,)
        )

        book = cursor.fetchone()

        if not book:
            return jsonify({
                "message": "Book not found"
            }), 404

        if book["available_copies"] <= 0:
            return jsonify({
                "message": "No copies available"
            }), 400

        borrow_date = date.today()
        due_date = borrow_date + timedelta(days=14)

        cursor.execute(
            """
            INSERT INTO borrows
            (member_id, book_id, borrow_date, due_date)
            VALUES (%s,%s,%s,%s)
            """,
            (
                member_id,
                book_id,
                borrow_date,
                due_date
            )
        )

        cursor.execute(
            """
            UPDATE books
            SET available_copies = available_copies - 1
            WHERE id=%s
            """,
            (book_id,)
        )

        conn.commit()

        return jsonify({
            "message": "Book borrowed successfully",
            "borrow_date": str(borrow_date),
            "due_date": str(due_date)
        }), 201

    finally:
        cursor.close()
        conn.close()


# ------------------------------------------------------------------
# Return Book
# ------------------------------------------------------------------

@borrows_bp.route("/return/<int:borrow_id>", methods=["POST"])
@login_required
@role_required("admin", "librarian")
def return_book(borrow_id):

    conn, cursor = get_db()

    try:

        cursor.execute(
            "SELECT * FROM borrows WHERE id=%s",
            (borrow_id,)
        )

        borrow = cursor.fetchone()

        if not borrow:
            return jsonify({
                "message": "Borrow record not found"
            }), 404

        if borrow["status"] == "returned":
            return jsonify({
                "message": "Book already returned"
            }), 400

        return_date = date.today()

        cursor.execute(
            """
            UPDATE borrows
            SET return_date=%s,
                status='returned'
            WHERE id=%s
            """,
            (return_date, borrow_id)
        )

        cursor.execute(
            """
            UPDATE books
            SET available_copies = available_copies + 1
            WHERE id=%s
            """,
            (borrow["book_id"],)
        )

        fine_amount = 0

        overdue_days = (return_date - borrow["due_date"]).days

        if overdue_days > 0:

            fine_amount = overdue_days * 5

            cursor.execute(
                """
                INSERT INTO fines
                (borrow_id, member_id, amount)
                VALUES (%s,%s,%s)
                """,
                (
                    borrow_id,
                    borrow["member_id"],
                    fine_amount
                )
            )

        conn.commit()

        return jsonify({
            "message": "Book returned successfully",
            "fine_amount": fine_amount
        })

    finally:
        cursor.close()
        conn.close()


# ------------------------------------------------------------------
# Active Borrows
# ------------------------------------------------------------------

@borrows_bp.route("/borrows/active", methods=["GET"])
@login_required
@role_required("admin", "librarian")
def active_borrows():

    conn, cursor = get_db()

    try:

        cursor.execute("""
            SELECT
                b.id,
                m.full_name,
                bk.title,
                b.borrow_date,
                b.due_date
            FROM borrows b
            JOIN members m
                ON b.member_id = m.id
            JOIN books bk
                ON b.book_id = bk.id
            WHERE b.status='active'
        """)

        borrows = cursor.fetchall()

        return jsonify({
            "success": True,
            "data": borrows
        })

    finally:
        cursor.close()
        conn.close()


# ------------------------------------------------------------------
# Overdue Borrows
# ------------------------------------------------------------------

@borrows_bp.route("/borrows/overdue", methods=["GET"])
@login_required
@role_required("admin", "librarian")
def overdue_borrows():

    conn, cursor = get_db()

    try:

        cursor.execute("""
            SELECT
                b.id,
                m.full_name,
                bk.title,
                b.borrow_date,
                b.due_date
            FROM borrows b
            JOIN members m
                ON b.member_id = m.id
            JOIN books bk
                ON b.book_id = bk.id
            WHERE b.status='active'
            AND b.due_date < CURDATE()
        """)

        overdue = cursor.fetchall()

        return jsonify({
            "success": True,
            "data": overdue
        })

    finally:
        cursor.close()
        conn.close()


# ------------------------------------------------------------------
# Member Borrow Book
# ------------------------------------------------------------------

@borrows_bp.route("/member-borrow", methods=["POST"])
@login_required
def member_borrow_book():

    data = request.get_json()
    book_id = data.get("book_id")

    if not book_id:
        return jsonify({
            "message": "book_id is required"
        }), 400

    conn, cursor = get_db()

    try:

        user_id = session.get("user_id")

        cursor.execute(
            "SELECT id FROM members WHERE user_id=%s",
            (user_id,)
        )

        member = cursor.fetchone()

        if not member:
            return jsonify({
                "message": "Member profile not found"
            }), 404

        member_id = member["id"]

        borrow_date = date.today()
        due_date = borrow_date + timedelta(days=14)

        cursor.execute(
            """
            INSERT INTO borrows
            (member_id, book_id, borrow_date, due_date)
            VALUES (%s,%s,%s,%s)
            """,
            (
                member_id,
                book_id,
                borrow_date,
                due_date
            )
        )

        cursor.execute(
            """
            UPDATE books
            SET available_copies = available_copies - 1
            WHERE id=%s
            """,
            (book_id,)
        )

        conn.commit()

        return jsonify({
            "message": "Book borrowed successfully",
            "borrow_date": str(borrow_date),
            "due_date": str(due_date)
        }), 201

    finally:
        cursor.close()
        conn.close()