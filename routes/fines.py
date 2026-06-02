from flask import Blueprint, jsonify
from datetime import date
from config import get_db
from routes.auth import login_required, role_required

fines_bp = Blueprint("fines", __name__)

# ---------------------------------------------------------------------------
# GET /fines — View all fines
# ---------------------------------------------------------------------------

@fines_bp.route("/fines", methods=["GET"])
@login_required
@role_required("admin", "librarian")
def get_fines():
    conn, cursor = get_db()
    try:
        cursor.execute(
            """
            SELECT
                f.id            AS fine_id,
                m.full_name     AS member_name,
                m.email         AS member_email,
                bk.title        AS book_title,
                f.amount,
                f.is_paid,
                f.paid_on
            FROM fines f
            JOIN members m  ON m.id  = f.member_id
            JOIN borrows b  ON b.id  = f.borrow_id
            JOIN books   bk ON bk.id = b.book_id
            ORDER BY f.is_paid ASC, f.id DESC
            """
        )
        fines = cursor.fetchall()
        return jsonify({
            "total_fines": len(fines),
            "fines": fines
        }), 200
    finally:
        cursor.close()
        conn.close()


# ---------------------------------------------------------------------------
# GET /fines/unpaid — View only unpaid fines
# ---------------------------------------------------------------------------

@fines_bp.route("/fines/unpaid", methods=["GET"])
@login_required
@role_required("admin", "librarian")
def get_unpaid_fines():
    conn, cursor = get_db()
    try:
        cursor.execute(
            """
            SELECT
                f.id            AS fine_id,
                m.full_name     AS member_name,
                m.email         AS member_email,
                bk.title        AS book_title,
                f.amount,
                f.is_paid
            FROM fines f
            JOIN members m  ON m.id  = f.member_id
            JOIN borrows b  ON b.id  = f.borrow_id
            JOIN books   bk ON bk.id = b.book_id
            WHERE f.is_paid = FALSE
            ORDER BY f.id DESC
            """
        )
        fines = cursor.fetchall()
        return jsonify({
            "total_unpaid": len(fines),
            "fines": fines
        }), 200
    finally:
        cursor.close()
        conn.close()


# ---------------------------------------------------------------------------
# GET /fines/collected — Total fines collected (paid)
# ---------------------------------------------------------------------------

@fines_bp.route("/fines/collected", methods=["GET"])
@login_required
@role_required("admin", "librarian")
def fines_collected():
    conn, cursor = get_db()
    try:
        cursor.execute(
            "SELECT SUM(amount) AS total_collected FROM fines WHERE is_paid=TRUE"
        )
        result = cursor.fetchone()
        total  = result["total_collected"] or 0
        return jsonify({
            "total_collected": float(total)
        }), 200
    finally:
        cursor.close()
        conn.close()


# ---------------------------------------------------------------------------
# POST /fines/<id>/pay — Mark a fine as paid
# ---------------------------------------------------------------------------

@fines_bp.route("/fines/<int:fine_id>/pay", methods=["POST"])
@login_required
@role_required("admin", "librarian")
def pay_fine(fine_id):
    conn, cursor = get_db()
    try:
        cursor.execute("SELECT * FROM fines WHERE id=%s", (fine_id,))
        fine = cursor.fetchone()
        if not fine:
            return jsonify({"message": "Fine not found"}), 404

        if fine["is_paid"]:
            return jsonify({"message": "Fine already paid"}), 400

        cursor.execute(
            "UPDATE fines SET is_paid=TRUE, paid_on=%s WHERE id=%s",
            (date.today(), fine_id)
        )
        conn.commit()
        return jsonify({
            "message": "Fine marked as paid",
            "fine_id": fine_id,
            "amount":  str(fine["amount"]),
            "paid_on": str(date.today())
        }), 200

    finally:
        cursor.close()
        conn.close()