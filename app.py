from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os
from dotenv import load_dotenv
from pwdlib import PasswordHash

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SESSION_SECRET", "change-this-secret")

DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "installation.db")
password_hash = PasswordHash.recommended()


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            place TEXT NOT NULL,
            purpose TEXT NOT NULL,
            users TEXT NOT NULL,
            message TEXT,
            status TEXT DEFAULT 'Pending'
        )
    """)
    conn.commit()
    conn.close()


init_db()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/submit", methods=["POST"])
def submit():
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    email = request.form.get("email", "").strip()
    place = request.form.get("place", "").strip()
    purpose = request.form.get("purpose", "").strip()
    users = request.form.get("users", "").strip()
    message = request.form.get("message", "").strip()

    conn = get_db()
    conn.execute(
        """INSERT INTO requests
        (name, phone, email, place, purpose, users, message, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (name, phone, email, place, purpose, users, message, "Pending")
    )
    conn.commit()
    conn.close()

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Solar Pure</title>
        <meta name="viewport" content="width=device-width,initial-scale=1">
        <style>
            body {{ font-family:Arial; background:#eefbfe; min-height:100vh; display:grid; place-items:center; margin:0; }}
            .card {{ background:#fff; padding:45px; border-radius:20px; text-align:center; box-shadow:0 18px 45px rgba(5,72,105,.14); max-width:520px; }}
            h1 {{ color:#063970; }} p {{ color:#60758a; }}
            a {{ display:inline-block; margin-top:15px; background:#063970; color:#fff; padding:12px 22px; border-radius:8px; text-decoration:none; font-weight:700; }}
        </style>
    </head>
    <body><div class="card"><h1>✓ Request Submitted</h1>
    <p>Thank you, {name}. Your Solar Pure installation request has been received.</p>
    <a href="/">Back to Solar Pure</a></div></body></html>
    """


@app.route("/admin")
def admin():
    return redirect(url_for("admin_login"))


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        admin_username = os.getenv("ADMIN_USERNAME")
        admin_password_hash = os.getenv("ADMIN_PASSWORD_HASH")

        valid = False
        if admin_password_hash:
            try:
                valid = password_hash.verify(password, admin_password_hash)
            except Exception:
                valid = False

        if username == admin_username and valid:
            session["admin_logged_in"] = True
            return redirect(url_for("dashboard"))

        return render_template("admin_login.html", error="Invalid username or password"), 401

    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/dashboard")
def dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    conn = get_db()
    rows = conn.execute("SELECT * FROM requests ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("admin_dashboard.html", rows=rows)


@app.route("/approve/<int:id>")
def approve(id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    conn = get_db()
    conn.execute("UPDATE requests SET status = 'Approved' WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))


@app.route("/delete/<int:id>")
def delete(id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    conn = get_db()
    conn.execute("DELETE FROM requests WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    app.run(debug=True)
