from flask import Blueprint, request, jsonify
from config import get_db
from routes.auth import login_required, role_required
 
members_bp = Blueprint("members", __name__)
 
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
            LEFT JOIN borrows b
                   ON b.member_id = m.id AND b.status = 'active'
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
 
    conn, cursor = get_db()
    try:
        cursor.execute("SELECT * FROM members WHERE id=%s", (member_id,))
        member = cursor.fetchone()
        if not member:
            return jsonify({"message": "Member not found"}), 404
 
        full_name = data.get("full_name", member["full_name"]).strip()
        email     = data.get("email", member["email"]).strip()
        phone     = data.get("phone", member["phone"])
        is_active = data.get("is_active", member["is_active"])
 
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
        if not is_active:
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