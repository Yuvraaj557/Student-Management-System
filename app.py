"""Student Management System - Flask backend with SQLite.

Run:  python app.py   ->  http://127.0.0.1:5000
"""
import os
import re
import sqlite3

from flask import Flask, g, jsonify, request, send_from_directory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB = os.path.join(BASE_DIR, "students.db")

app = Flask(__name__, static_folder="static", static_url_path="/static")
app.config["DATABASE"] = DEFAULT_DB

SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL,
    roll_no    TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    class_name TEXT    NOT NULL,
    marks      REAL    NOT NULL CHECK (marks >= 0 AND marks <= 100),
    contact    TEXT    NOT NULL,
    created_at TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_students_name ON students(name);
"""


# ---------- database helpers ----------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with sqlite3.connect(app.config["DATABASE"]) as conn:
        conn.executescript(SCHEMA)


def row_to_dict(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "roll_no": row["roll_no"],
        "class_name": row["class_name"],
        "marks": row["marks"],
        "contact": row["contact"],
    }


# ---------- validation ----------
def validate(data):
    """Return (clean_data, errors). Errors is a dict of field -> message."""
    errors = {}
    if not isinstance(data, dict):
        return None, {"_": "Request body must be JSON."}

    name = str(data.get("name", "")).strip()
    roll_no = str(data.get("roll_no", "")).strip()
    class_name = str(data.get("class_name", "")).strip()
    contact = str(data.get("contact", "")).strip()

    if len(name) < 2:
        errors["name"] = "Enter the student's full name (at least 2 characters)."
    elif not re.fullmatch(r"[A-Za-z][A-Za-z .'-]*", name):
        errors["name"] = "Name can contain only letters, spaces, and . ' -"

    if not roll_no:
        errors["roll_no"] = "Enter a roll number."
    elif not re.fullmatch(r"[A-Za-z0-9/_-]{1,20}", roll_no):
        errors["roll_no"] = "Roll number can use letters, digits, / _ - (max 20)."

    if not class_name:
        errors["class_name"] = "Enter the class, for example B.Tech CSE."

    try:
        marks = float(data.get("marks"))
        if not 0 <= marks <= 100:
            raise ValueError
    except (TypeError, ValueError):
        marks = None
        errors["marks"] = "Marks must be a number between 0 and 100."

    if not re.fullmatch(r"[6-9]\d{9}", contact):
        errors["contact"] = "Contact must be a 10-digit mobile number starting with 6-9."

    if errors:
        return None, errors
    return {
        "name": name,
        "roll_no": roll_no,
        "class_name": class_name,
        "marks": round(marks, 2),
        "contact": contact,
    }, {}


def error(message, status=400, fields=None):
    body = {"error": message}
    if fields:
        body["fields"] = fields
    return jsonify(body), status


@app.after_request
def add_cors_headers(resp):
    """Allow the page to call the API even if it was opened from a file."""
    if request.path.startswith("/api/"):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    return resp


# ---------- pages ----------
@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


# ---------- REST API ----------
@app.route("/api/students", methods=["GET"])
def list_students():
    q = request.args.get("q", "").strip()
    db = get_db()
    if q:
        like = f"%{q}%"
        rows = db.execute(
            """SELECT * FROM students
               WHERE name LIKE ? OR roll_no LIKE ? OR class_name LIKE ?
               ORDER BY id DESC""",
            (like, like, like),
        ).fetchall()
    else:
        rows = db.execute("SELECT * FROM students ORDER BY id DESC").fetchall()
    return jsonify([row_to_dict(r) for r in rows])


@app.route("/api/students/<int:student_id>", methods=["GET"])
def get_student(student_id):
    row = get_db().execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    if row is None:
        return error("Student not found.", 404)
    return jsonify(row_to_dict(row))


@app.route("/api/students", methods=["POST"])
def add_student():
    clean, errors = validate(request.get_json(silent=True))
    if errors:
        return error("Please fix the highlighted fields.", 400, errors)
    db = get_db()
    try:
        cur = db.execute(
            "INSERT INTO students (name, roll_no, class_name, marks, contact) VALUES (?,?,?,?,?)",
            (clean["name"], clean["roll_no"], clean["class_name"], clean["marks"], clean["contact"]),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return error("Roll number already exists.", 409, {"roll_no": "This roll number is already taken."})
    row = db.execute("SELECT * FROM students WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify(row_to_dict(row)), 201


@app.route("/api/students/<int:student_id>", methods=["PUT"])
def update_student(student_id):
    db = get_db()
    if db.execute("SELECT 1 FROM students WHERE id = ?", (student_id,)).fetchone() is None:
        return error("Student not found.", 404)
    clean, errors = validate(request.get_json(silent=True))
    if errors:
        return error("Please fix the highlighted fields.", 400, errors)
    try:
        db.execute(
            "UPDATE students SET name=?, roll_no=?, class_name=?, marks=?, contact=? WHERE id=?",
            (clean["name"], clean["roll_no"], clean["class_name"], clean["marks"], clean["contact"], student_id),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return error("Roll number already exists.", 409, {"roll_no": "This roll number is already taken."})
    row = db.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    return jsonify(row_to_dict(row))


@app.route("/api/students/<int:student_id>", methods=["DELETE"])
def delete_student(student_id):
    db = get_db()
    cur = db.execute("DELETE FROM students WHERE id = ?", (student_id,))
    db.commit()
    if cur.rowcount == 0:
        return error("Student not found.", 404)
    return jsonify({"message": "Student deleted."})


@app.route("/api/stats", methods=["GET"])
def stats():
    row = get_db().execute(
        "SELECT COUNT(*) AS total, AVG(marks) AS avg, MAX(marks) AS top FROM students"
    ).fetchone()
    return jsonify({
        "total": row["total"],
        "average": round(row["avg"], 2) if row["avg"] is not None else 0,
        "top": row["top"] if row["top"] is not None else 0,
    })


init_db()

def find_free_port(start=5000, tries=20):
    import socket
    for port in range(start, start + tries):
        with socket.socket() as sock:
            if sock.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return start


if __name__ == "__main__":
    import threading
    import webbrowser

    port = int(os.environ.get("PORT", find_free_port(5000)))
    url = f"http://127.0.0.1:{port}"
    print("\n" + "=" * 56)
    print("  Student Management System is running")
    print(f"  Open this address in your browser:  {url}")
    print("  Keep this window open. Press Ctrl+C to stop.")
    print("=" * 56 + "\n")
    threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    app.run(host="127.0.0.1", port=port, debug=False)
