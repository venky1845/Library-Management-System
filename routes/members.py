from flask import Blueprint, request, jsonify, session
from datetime import date
from config import get_db
from routes.auth import login_required, role_required
 
members_bp = Blueprint("members", __name__)


@members_bp.route("/me", methods=["GET"])
@login_required
def me():
    """Return current logged-in user's id and role."""
    conn, cursor = get_db()
    try:
        user_id = session.get("user_id")
        cursor.execute("SELECT id, role FROM users WHERE id=%s", (user_id,))
        user = cursor.fetchone()
        if not user:
            return jsonify({"message": "User not found"}), 404
        return jsonify({"user_id": user["id"], "role": user["role"]}), 200
    finally:
        cursor.close()
        conn.close()
 
@members_bp.route("/members", methods=["POST"])
@login_required
@role_required("admin", "librarian")
def add_member():
    data = request.get_json()
 
    user_id   = data.get("user_id")
    full_name = data.get("full_name", "").strip()
    email     = data.get("email", "").strip()
    phone     = data.get("phone", "").strip()
 
    if not full_name or not email:
        return jsonify({"message": "Full name and email are required"}), 400
 
    conn, cursor = get_db()
    try:
        # Check if user_id exists in users table
        if user_id:
            cursor.execute("SELECT id FROM users WHERE id=%s", (user_id,))
            if not cursor.fetchone():
                return jsonify({"message": "User not found"}), 404
 
        # Check duplicate email
        cursor.execute("SELECT id FROM members WHERE email=%s", (email,))
        if cursor.fetchone():
            return jsonify({"message": "Member with this email already exists"}), 400
 
        # Check duplicate user_id
        if user_id:
            cursor.execute("SELECT id FROM members WHERE user_id=%s", (user_id,))
            if cursor.fetchone():
                return jsonify({"message": "This user is already registered as a member"}), 400
 
        cursor.execute(
            """
            INSERT INTO members (user_id, full_name, email, phone)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id or None, full_name, email, phone or None)
        )
        conn.commit()
        return jsonify({"message": "Member registered successfully"}), 201
 
    finally:
        cursor.close()
        conn.close()
 
 
@members_bp.route("/members", methods=["GET"])
@login_required
@role_required("admin", "librarian")
def get_members():
    conn, cursor = get_db()
    try:
        cursor.execute(
            """
            SELECT m.*,
                   COUNT(b.id) AS active_borrow_count
            FROM members m
            LEFT JOIN users u
                   ON u.id = m.user_id
            LEFT JOIN borrows b
                   ON b.member_id = m.id AND b.status = 'active'
            WHERE m.user_id IS NULL OR u.role = 'member'
            GROUP BY m.id
            """
        )
        members = cursor.fetchall()
        return jsonify(members), 200
    finally:
        cursor.close()
        conn.close()
 
 
 
@members_bp.route("/members/<int:member_id>", methods=["GET"])
@login_required
@role_required("admin", "librarian")
def get_member(member_id):
    conn, cursor = get_db()
    try:
        cursor.execute(
            """
            SELECT m.*,
                   COUNT(b.id) AS active_borrow_count
            FROM members m
            LEFT JOIN borrows b
                   ON b.member_id = m.id AND b.status = 'active'
            WHERE m.id = %s
            GROUP BY m.id
            """,
            (member_id,)
        )
        member = cursor.fetchone()
        if not member:
            return jsonify({"message": "Member not found"}), 404
        return jsonify(member), 200
    finally:
        cursor.close()
        conn.close()
 
 
@members_bp.route("/members/<int:member_id>", methods=["PUT"])
@login_required
@role_required("admin", "librarian")
def update_member(member_id):
    data = request.get_json()
    caller_role = session.get("role")

    conn, cursor = get_db()
    try:
        cursor.execute("SELECT * FROM members WHERE id=%s", (member_id,))
        member = cursor.fetchone()
        if not member:
            return jsonify({"message": "Member not found"}), 404

        full_name = data.get("full_name", member["full_name"]).strip()
        email     = data.get("email", member["email"]).strip()
        phone     = data.get("phone", member["phone"])

        # Only admin can change is_active (deactivate/reactivate)
        if caller_role == "admin":
            is_active = data.get("is_active", member["is_active"])
        else:
            is_active = member["is_active"]  # librarian keeps existing status

        if not full_name or not email:
            return jsonify({"message": "Full name and email are required"}), 400

        # Check duplicate email (excluding current member)
        cursor.execute(
            "SELECT id FROM members WHERE email=%s AND id != %s",
            (email, member_id)
        )
        if cursor.fetchone():
            return jsonify({"message": "Another member with this email already exists"}), 400

        cursor.execute(
            """
            UPDATE members
            SET full_name=%s, email=%s, phone=%s, is_active=%s
            WHERE id=%s
            """,
            (full_name, email, phone, is_active, member_id)
        )
        conn.commit()

        action = "updated"
        if caller_role == "admin" and not is_active:
            action = "deactivated"

        return jsonify({"message": f"Member {action} successfully"}), 200

    finally:
        cursor.close()
        conn.close()
 
 
@members_bp.route("/members/<int:member_id>/history", methods=["GET"])
@login_required
@role_required("admin", "librarian")
def member_history(member_id):
    conn, cursor = get_db()
    try:
        # Check member exists
        cursor.execute("SELECT id FROM members WHERE id=%s", (member_id,))
        if not cursor.fetchone():
            return jsonify({"message": "Member not found"}), 404
 
        cursor.execute(
            """
            SELECT
                b.id          AS borrow_id,
                bk.title      AS book_title,
                bk.author     AS book_author,
                b.borrow_date,
                b.due_date,
                b.return_date,
                b.status,
                f.amount      AS fine_amount,
                f.is_paid     AS fine_paid
            FROM borrows b
            JOIN books bk ON bk.id = b.book_id
            LEFT JOIN fines f ON f.borrow_id = b.id
            WHERE b.member_id = %s
            ORDER BY b.borrow_date DESC
            """,
            (member_id,)
        )
        history = cursor.fetchall()
        return jsonify({
            "member_id": member_id,
            "total_borrows": len(history),
            "history": history
        }), 200
 
    finally:
        cursor.close()
        conn.close()
 
 
@members_bp.route("/my-profile", methods=["GET"])
@login_required
def my_profile():
    """Get current logged-in member's profile"""
    conn, cursor = get_db()
    try:
        # Member login sets member_id directly in session
        if "member_id" in session:
            cursor.execute(
                """
                SELECT m.*,
                       COUNT(b.id) AS active_borrow_count
                FROM members m
                LEFT JOIN borrows b
                       ON b.member_id = m.id AND b.status = 'active'
                WHERE m.id = %s
                GROUP BY m.id
                """,
                (session["member_id"],)
            )
        else:
            # Staff/user account linked member
            cursor.execute(
                """
                SELECT m.*,
                       COUNT(b.id) AS active_borrow_count
                FROM members m
                LEFT JOIN borrows b
                       ON b.member_id = m.id AND b.status = 'active'
                WHERE m.user_id = %s
                GROUP BY m.id
                """,
                (session.get("user_id"),)
            )
        member = cursor.fetchone()
        if not member:
            return jsonify({"message": "Member profile not found"}), 404
        return jsonify(member), 200
    finally:
        cursor.close()
        conn.close()


@members_bp.route("/my-borrows", methods=["GET"])
@login_required
def my_borrows():
    """Get current member's borrow history"""
    conn, cursor = get_db()
    try:
        # Resolve member_id from session
        if "member_id" in session:
            member_id = session["member_id"]
        else:
            cursor.execute("SELECT id FROM members WHERE user_id=%s", (session.get("user_id"),))
            member = cursor.fetchone()
            if not member:
                return jsonify({"message": "Member profile not found"}), 404
            member_id = member["id"]
        today = date.today()
        
        cursor.execute(
            """
            SELECT
                b.id                AS borrow_id,
                bk.id               AS book_id,
                bk.title            AS book_title,
                bk.author           AS book_author,
                b.borrow_date,
                b.due_date,
                b.return_date,
                b.status,
                CASE 
                    WHEN b.status = 'active' AND b.due_date < %s THEN DATEDIFF(%s, b.due_date)
                    ELSE 0
                END AS days_overdue,
                CASE
                    WHEN b.status = 'active' AND b.due_date < %s THEN DATEDIFF(%s, b.due_date) * 5
                    ELSE 0
                END AS fine_if_returned_today
            FROM borrows b
            JOIN books bk ON bk.id = b.book_id
            WHERE b.member_id = %s
            ORDER BY b.borrow_date DESC
            """,
            (today, today, today, today, member_id)
        )
        borrows = cursor.fetchall()
        
        active_count = sum(1 for b in borrows if b["status"] == "active")
        overdue_count = sum(1 for b in borrows if b["status"] == "active" and b["days_overdue"] > 0)
        
        return jsonify({
            "total_borrows": len(borrows),
            "active_borrows": active_count,
            "overdue_borrows": overdue_count,
            "borrows": borrows
        }), 200
    finally:
        cursor.close()
        conn.close()


@members_bp.route("/my-fines", methods=["GET"])
@login_required
def my_fines():
    """Get current member's fine status"""
    conn, cursor = get_db()
    try:
        # Resolve member_id from session
        if "member_id" in session:
            member_id = session["member_id"]
        else:
            cursor.execute("SELECT id FROM members WHERE user_id=%s", (session.get("user_id"),))
            member = cursor.fetchone()
            if not member:
                return jsonify({"message": "Member profile not found"}), 404
            member_id = member["id"]
        
        # Get all fines for this member
        cursor.execute(
            """
            SELECT
                f.id            AS fine_id,
                bk.title        AS book_title,
                bk.author       AS book_author,
                b.due_date,
                b.return_date,
                f.amount,
                f.is_paid,
                f.paid_on
            FROM fines f
            JOIN borrows b  ON b.id  = f.borrow_id
            JOIN books   bk ON bk.id = b.book_id
            WHERE f.member_id = %s
            ORDER BY f.is_paid ASC, f.id DESC
            """,
            (member_id,)
        )
        fines = cursor.fetchall()
        
        # Calculate summary
        total_fines = len(fines)
        unpaid_fines = sum(1 for f in fines if not f["is_paid"])
        total_amount = sum(float(f["amount"]) for f in fines)
        unpaid_amount = sum(float(f["amount"]) for f in fines if not f["is_paid"])
        
        return jsonify({
            "total_fines": total_fines,
            "unpaid_fines": unpaid_fines,
            "total_amount": float(total_amount),
            "unpaid_amount": float(unpaid_amount),
            "fines": fines
        }), 200
    finally:
        cursor.close()
        conn.close()

 
@members_bp.route("/members/<int:member_id>", methods=["DELETE"])
@login_required
@role_required("admin")
def deactivate_member(member_id):
    conn, cursor = get_db()
    try:
        cursor.execute("SELECT id FROM members WHERE id=%s", (member_id,))
        if not cursor.fetchone():
            return jsonify({"message": "Member not found"}), 404

        cursor.execute(
            "UPDATE members SET is_active=FALSE WHERE id=%s",
            (member_id,)
        )
        conn.commit()
        return jsonify({"message": "Member deactivated successfully"}), 200

    finally:
        cursor.close()
        conn.close()


@members_bp.route("/members/<int:member_id>/delete", methods=["DELETE"])
@login_required
@role_required("admin")
def delete_member(member_id):
    """Permanently delete a member (admin only)."""
    conn, cursor = get_db()
    try:
        cursor.execute("SELECT id FROM members WHERE id=%s", (member_id,))
        if not cursor.fetchone():
            return jsonify({"message": "Member not found"}), 404

        # Block deletion if member has active borrows
        cursor.execute(
            "SELECT COUNT(*) AS cnt FROM borrows WHERE member_id=%s AND status='active'",
            (member_id,)
        )
        if cursor.fetchone()["cnt"] > 0:
            return jsonify({"message": "Cannot delete member with active borrows"}), 400

        cursor.execute("DELETE FROM members WHERE id=%s", (member_id,))
        conn.commit()
        return jsonify({"message": "Member deleted permanently"}), 200

    finally:
        cursor.close()
        conn.close()