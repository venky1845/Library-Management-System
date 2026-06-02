import os
from flask import Flask, send_from_directory
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from dotenv import load_dotenv

from routes.auth    import auth_bp
from routes.books   import books_bp
from routes.members import members_bp
from routes.borrows import borrows_bp
from routes.fines   import fines_bp

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY", os.urandom(24))

bcrypt = Bcrypt(app)

CORS(app, supports_credentials=True)

app.register_blueprint(auth_bp)
app.register_blueprint(books_bp)
app.register_blueprint(members_bp)
app.register_blueprint(borrows_bp)
app.register_blueprint(fines_bp)

@app.route("/")
def home():
    return send_from_directory(
        os.path.join(app.root_path, "static", "pages"),
        "login.html"
    )
@app.route("/register-page")
def register_page():
    return send_from_directory(
        os.path.join(app.root_path, "static", "pages"),
        "register.html"
    )
@app.route("/dashboard")
def dashboard():
    return send_from_directory("static/pages", "dashboard.html")

@app.route("/books-page")
def books_page():
    return send_from_directory("static/pages", "books.html")

@app.route("/members-page")
def members():
    return send_from_directory(
        os.path.join(app.root_path, "static", "pages"),
        "members.html"
    )

@app.route("/borrows-page")
def borrows_page():
    return send_from_directory("static/pages", "borrows.html")

@app.route("/fines-page")
def fines_page():
    return send_from_directory("static/pages", "fines.html")

# ---- Member-only routes ----
@app.route("/member-dashboard")
def member_dashboard():
    return send_from_directory("static/pages", "member-dashboard.html")

@app.route("/member-books")
def member_books():
    return send_from_directory("static/pages", "member-books.html")

@app.route("/member-borrows")
def member_borrows():
    return send_from_directory("static/pages", "member-borrows.html")

@app.route("/member-fines")
def member_fines():
    return send_from_directory("static/pages", "member-fines.html")

if __name__ == "__main__":
    app.run(debug=True)