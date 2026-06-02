import os
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from dotenv import load_dotenv
from routes.auth import auth_bp

from routes.books import books_bp
from routes.borrows import borrows_bp
from routes.fines import fines_bp

load_dotenv()

app = Flask(__name__)
app.register_blueprint(borrows_bp)
app.register_blueprint(fines_bp)
app.secret_key = os.getenv("SECRET_KEY", os.urandom(24))

bcrypt = Bcrypt(app)

CORS(app, supports_credentials=True)

app.register_blueprint(auth_bp)
app.register_blueprint(books_bp)

@app.route("/")
def home():
    return {
        "message": "Library Management System API Running"
    }

if __name__ == "__main__":
    app.run(debug=True)