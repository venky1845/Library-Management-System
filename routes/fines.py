from flask import Blueprint, jsonify
from config import get_db
from datetime import date
from datetime import datetime
fines_bp = Blueprint('fines', __name__)

# Return Book
@fines_bp.route('/return/<int:borrow_id>', methods=['POST'])
def return_book(borrow_id):

    conn, cursor = get_db()

    try:
        # Get borrow details
        cursor.execute("""
            SELECT *
            FROM borrows
            WHERE id = %s
        """, (borrow_id,))

        borrow = cursor.fetchone()

        if not borrow:
            return jsonify({
                "success": False,
                "message": "Borrow record not found"
            }), 404

        if borrow["status"] == "returned":
            return jsonify({
                "success": False,
                "message": "Book already returned"
            }), 400

        return_date = datetime.now()

        # Update borrow record
        cursor.execute("""
            UPDATE borrows
            SET return_date=%s,
                status='returned'
            WHERE id=%s
        """, (return_date, borrow_id))

        # Increase available copies
        cursor.execute("""
            UPDATE books
            SET available_copies = available_copies + 1
            WHERE id=%s
        """, (borrow["book_id"],))

        # Fine Calculation
        overdue_days = (return_date - borrow["due_date"]).days

        fine_amount = 0

        if overdue_days > 0:

            fine_amount = overdue_days * 5

            cursor.execute("""
                INSERT INTO fines
                (
                    borrow_id,
                    member_id,
                    amount
                )
                VALUES (%s,%s,%s)
            """, (
                borrow_id,
                borrow["member_id"],
                fine_amount
            ))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Book returned successfully",
            "fine_amount": fine_amount
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        cursor.close()
        conn.close()


# Pay Fine
@fines_bp.route('/fines/<int:fine_id>/pay', methods=['POST'])
def pay_fine(fine_id):

    conn, cursor = get_db()

    try:

        cursor.execute("""
            SELECT *
            FROM fines
            WHERE id=%s
        """, (fine_id,))

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
            SET is_paid=TRUE,
                paid_on=CURDATE()
            WHERE id=%s
        """, (fine_id,))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Fine paid successfully"
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        cursor.close()
        conn.close()


# View All Fines
@fines_bp.route('/fines', methods=['GET'])
def get_fines():

    conn, cursor = get_db()

    try:

        cursor.execute("""
            SELECT *
            FROM fines
            ORDER BY id DESC
        """)

        fines = cursor.fetchall()

        return jsonify({
            "success": True,
            "data": fines
        })

    finally:
        cursor.close()
        conn.close()