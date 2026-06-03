from flask import Blueprint, jsonify
from datetime import date
from config import get_db
from routes.auth import login_required, role_required

fines_bp = Blueprint("fines", __name__)

# --------------------------------------------------
# View All Fines
# --------------------------------------------------
@fines_bp.route("/fines", methods=["GET"])
@login_required
@role_required("admin", "librarian")
def get_fines():
    conn, cursor = get_db()

    try:
        cursor.execute("""
            SELECT
                f.id AS fine_id,
                m.full_name AS member_name,
                bk.title AS book_title,
                f.amount,
                f.is_paid,
                f.paid_on
            FROM fines f
            JOIN members m ON m.id = f.member_id
            JOIN borrows b ON b.id = f.borrow_id
            JOIN books bk ON bk.id = b.book_id
            ORDER BY f.id DESC
        """)

        fines = cursor.fetchall()

        return jsonify({
            "success": True,
            "total_fines": len(fines),
            "data": fines
        }), 200

    finally:
        cursor.close()
        conn.close()


# --------------------------------------------------
# View Unpaid Fines
# --------------------------------------------------
@fines_bp.route("/fines/unpaid", methods=["GET"])
@login_required
@role_required("admin", "librarian")
def get_unpaid_fines():
    conn, cursor = get_db()

    try:
        cursor.execute("""
            SELECT
                f.id AS fine_id,
                m.full_name AS member_name,
                bk.title AS book_title,
                f.amount
            FROM fines f
            JOIN members m ON m.id = f.member_id
            JOIN borrows b ON b.id = f.borrow_id
            JOIN books bk ON bk.id = b.book_id
            WHERE f.is_paid = FALSE
            ORDER BY f.id DESC
        """)

        fines = cursor.fetchall()

        return jsonify({
            "success": True,
            "total_unpaid": len(fines),
            "data": fines
        }), 200

    finally:
        cursor.close()
        conn.close()


# --------------------------------------------------
# Total Collected Fines
# --------------------------------------------------
@fines_bp.route("/fines/collected", methods=["GET"])
@login_required
@role_required("admin", "librarian")
def fines_collected():
    conn, cursor = get_db()

    try:
        cursor.execute("""
            SELECT SUM(amount) AS total_collected
            FROM fines
            WHERE is_paid = TRUE
        """)

        result = cursor.fetchone()

        return jsonify({
            "success": True,
            "total_collected": float(result["total_collected"] or 0)
        }), 200

    finally:
        cursor.close()
        conn.close()


# --------------------------------------------------
# Pay Fine
# --------------------------------------------------
@fines_bp.route("/fines/<int:fine_id>/pay", methods=["POST"])
@login_required
@role_required("admin", "librarian")
def pay_fine(fine_id):
    conn, cursor = get_db()

    try:
        cursor.execute(
            "SELECT * FROM fines WHERE id=%s",
            (fine_id,)
        )

        fine = cursor.fetchone()

        if not fine:
            return jsonify({
                "success": False,
                "message": "Fine not found"
            }), 404

        if fine["is_paid"]:
            return jsonify({
                "success": False,
                "message": "Fine already paid"
            }), 400

        cursor.execute("""
            UPDATE fines
            SET is_paid = TRUE,
                paid_on = %s
            WHERE id = %s
        """, (date.today(), fine_id))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Fine paid successfully",
            "fine_id": fine_id,
            "amount": str(fine["amount"]),
            "paid_on": str(date.today())
        }), 200

    finally:
        cursor.close()
        conn.close()