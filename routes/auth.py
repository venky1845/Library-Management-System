from flask import Blueprint, request, jsonify, session
from flask_bcrypt import generate_password_hash, check_password_hash
from functools import wraps

from config import get_db

auth_bp = Blueprint("auth", __name__)

# ---------------------------------------------------------------------------
# Decorators
# ---------------------------------------------------------------------------

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"message": "Login Required"}), 401
        return func(*args, **kwargs)
    return wrapper


def role_required(*roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if session.get("role") not in roles:
                return jsonify({"message": "Access Denied"}), 403
            return func(*args, **kwargs)
        return wrapper
    return decorator

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    # --- Input validation ---
    username = data.get("username", "").strip()
    email    = data.get("email", "").strip()
    password = data.get("password", "").strip()
    role     = data.get("role", "").strip()

    if not username or not email or not password:
        return jsonify({"message": "Username, email, and password are required"}), 400

    # --- Role is required and must be admin, librarian, or member ---
    valid_roles = ("admin", "librarian", "member")

    if not role:
        return jsonify({"message": "Role is required"}), 403

    if role not in valid_roles:
        return jsonify({"message": "Access Denied. Role must be admin, librarian, or member"}), 403

    conn, cursor = get_db()
    try:
        cursor.execute(
            "SELECT id FROM users WHERE username=%s OR email=%s",
            (username, email)
        )
        if cursor.fetchone():
            return jsonify({"message": "User already exists"}), 400

        hashed_password = generate_password_hash(password).decode("utf-8")

        cursor.execute(
            "INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)",
            (username, email, hashed_password, role)
        )
        
        # Get the newly created user_id
        user_id = cursor.lastrowid
        
        # If registering as member, create member profile automatically
        if role == "member":
            cursor.execute(
                "INSERT INTO members (user_id, full_name, email, phone) VALUES (%s, %s, %s, %s)",
                (user_id, username, email, None)
            )
        
        conn.commit()
        return jsonify({"message": "Registration Successful"}), 201

    finally:
        cursor.close()
        conn.close()


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    email    = (data.get("email") or "").strip()
    password = (data.get("password") or "").strip()

    if not email or not password:
        return jsonify({"message": "Email and password are required"}), 400

    conn, cursor = get_db()
    try:
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

    if not user:
        return jsonify({"message": "Invalid Email"}), 401

    if not check_password_hash(user["password"], password):
        return jsonify({"message": "Invalid Password"}), 401

    session["user_id"]  = user["id"]
    session["username"] = user["username"]
    session["role"]     = user["role"]

    return jsonify({"message": "Login Successful", "role": user["role"]})


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    return jsonify({"message": "Logout Successful"})


@auth_bp.route("/profile", methods=["GET"])
@login_required
def profile():
    return jsonify({
        "user_id":  session["user_id"],
        "username": session["username"],
        "role":     session["role"]
    })


@auth_bp.route("/admin", methods=["GET"])
@login_required
@role_required("admin")
def admin():
    return jsonify({"message": "Welcome Admin"})


@auth_bp.route("/librarian", methods=["GET"])
@login_required
@role_required("admin", "librarian")
def librarian():
    return jsonify({"message": "Welcome Librarian"})


@auth_bp.route("/member", methods=["GET"])
@login_required
@role_required("member")
def member():
    return jsonify({"message": "Welcome Member"})