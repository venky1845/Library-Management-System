from flask import Blueprint, request, jsonify
from config import get_db
from datetime import datetime, timedelta

borrows_bp = Blueprint('borrows', __name__)
borrow_date = datetime.now()
due_date = borrow_date + timedelta(days=14)
# Borrow a Book
@borrows_bp.route('/borrow', methods=['POST'])
def borrow_book():
    conn, cursor = get_db()

    try:
        data = request.get_json()

        member_id = data.get("member_id")
        book_id = data.get("book_id")

        if not member_id or not book_id:
            return jsonify({
                "success": False,
                "message": "member_id and book_id are required"
            }), 400

        # Check unpaid fines
        cursor.execute("""
            SELECT *
            FROM fines
            WHERE member_id = %s
            AND is_paid = FALSE
        """, (member_id,))

        unpaid_fine = cursor.fetchone()

        if unpaid_fine:
            return jsonify({
                "success": False,
                "message": "Member has unpaid fines"
            }), 400

        # Check book availability
        cursor.execute("""
            SELECT *
            FROM books
            WHERE id = %s
        """, (book_id,))

        book = cursor.fetchone()

        if not book:
            return jsonify({
                "success": False,
                "message": "Book not found"
            }), 404

        if book["available_copies"] <= 0:
            return jsonify({
                "success": False,
                "message": "No copies available"
            }), 400

        borrow_date = datetime.now()
        due_date = borrow_date + timedelta(days=14)

        # Create borrow record
        cursor.execute("""
            INSERT INTO borrows
            (
                member_id,
                book_id,
                borrow_date,
                due_date
            )
            VALUES (%s,%s,%s,%s)
        """, (
            member_id,
            book_id,
            borrow_date,
            due_date
        ))

        # Reduce available copies
        cursor.execute("""
            UPDATE books
            SET available_copies = available_copies - 1
            WHERE id = %s
        """, (book_id,))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Book borrowed successfully",
            "borrow_date": borrow_date.strftime("%Y-%m-%d %H:%M:%S"),
            "due_date": due_date.strftime("%Y-%m-%d %H:%M:%S")
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        cursor.close()
        conn.close()


# Get Active Borrows
@borrows_bp.route('/borrows/active', methods=['GET'])
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
            WHERE b.status = 'active'
        """)

        borrows = cursor.fetchall()

        for borrow in borrows:
            borrow["borrow_date"] = borrow["borrow_date"].strftime("%Y-%m-%d")
            borrow["due_date"] = borrow["due_date"].strftime("%Y-%m-%d")

        return jsonify({
            "success": True,
            "data": borrows
        })
        
    finally:
        cursor.close()
        conn.close()


# Get Overdue Borrows
@borrows_bp.route('/borrows/overdue', methods=['GET'])
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