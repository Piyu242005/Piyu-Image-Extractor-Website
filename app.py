from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-secret-key")
DATABASE = os.path.join(os.path.dirname(__file__), "tasks.db")


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT DEFAULT '',
        status TEXT NOT NULL DEFAULT 'todo',
        priority TEXT NOT NULL DEFAULT 'medium',
        due_date TEXT DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)
    conn.commit()
    conn.close()


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return user


@app.context_processor
def inject_user():
    return {"current_user": current_user()}


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 6:
            flash("Enter a name, valid email, and password of at least 6 characters.", "error")
            return render_template("register.html")
        conn = get_db()
        try:
            cursor = conn.execute(
                "INSERT INTO users(name,email,password_hash,created_at) VALUES(?,?,?,?)",
                (name, email, generate_password_hash(password), datetime.utcnow().isoformat())
            )
            conn.commit()
            session["user_id"] = cursor.lastrowid
        except sqlite3.IntegrityError:
            flash("An account with that email already exists.", "error")
            conn.close()
            return render_template("register.html")
        conn.close()
        return redirect(url_for("dashboard"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db()
    tasks = conn.execute(
        "SELECT * FROM tasks WHERE user_id = ? ORDER BY CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, created_at DESC",
        (session["user_id"],)
    ).fetchall()
    conn.close()
    return render_template("dashboard.html", tasks=tasks)


@app.route("/tasks", methods=["POST"])
@login_required
def create_task():
    data = request.get_json(silent=True) or request.form
    title = str(data.get("title", "")).strip()
    description = str(data.get("description", "")).strip()
    status = str(data.get("status", "todo"))
    priority = str(data.get("priority", "medium"))
    due_date = str(data.get("due_date", "")).strip()

    if not title:
        return jsonify({"error": "Task title is required."}), 400
    if status not in {"todo", "in_progress", "done"} or priority not in {"low", "medium", "high"}:
        return jsonify({"error": "Invalid task fields."}), 400

    now = datetime.utcnow().isoformat()
    conn = get_db()
    cursor = conn.execute(
        """INSERT INTO tasks(user_id,title,description,status,priority,due_date,created_at,updated_at)
           VALUES(?,?,?,?,?,?,?,?)""",
        (session["user_id"], title, description, status, priority, due_date, now, now)
    )
    conn.commit()
    task = conn.execute("SELECT * FROM tasks WHERE id = ?", (cursor.lastrowid,)).fetchone()
    conn.close()
    return jsonify(dict(task)), 201


@app.route("/tasks/<int:task_id>", methods=["PUT"])
@login_required
def update_task(task_id):
    data = request.get_json(silent=True) or {}
    conn = get_db()
    task = conn.execute("SELECT * FROM tasks WHERE id = ? AND user_id = ?", (task_id, session["user_id"])).fetchone()
    if not task:
        conn.close()
        return jsonify({"error": "Task not found."}), 404

    title = str(data.get("title", task["title"])).strip()
    description = str(data.get("description", task["description"])).strip()
    status = str(data.get("status", task["status"]))
    priority = str(data.get("priority", task["priority"]))
    due_date = str(data.get("due_date", task["due_date"])).strip()

    if not title or status not in {"todo", "in_progress", "done"} or priority not in {"low", "medium", "high"}:
        conn.close()
        return jsonify({"error": "Invalid task fields."}), 400

    conn.execute(
        """UPDATE tasks SET title=?, description=?, status=?, priority=?, due_date=?, updated_at=?
           WHERE id=? AND user_id=?""",
        (title, description, status, priority, due_date, datetime.utcnow().isoformat(), task_id, session["user_id"])
    )
    conn.commit()
    updated = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    return jsonify(dict(updated))


@app.route("/tasks/<int:task_id>", methods=["DELETE"])
@login_required
def delete_task(task_id):
    conn = get_db()
    result = conn.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, session["user_id"]))
    conn.commit()
    conn.close()
    if result.rowcount == 0:
        return jsonify({"error": "Task not found."}), 404
    return jsonify({"success": True})


@app.route("/api/tasks")
@login_required
def api_tasks():
    conn = get_db()
    tasks = conn.execute(
        "SELECT * FROM tasks WHERE user_id = ? ORDER BY created_at DESC",
        (session["user_id"],)
    ).fetchall()
    conn.close()
    return jsonify([dict(task) for task in tasks])


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/features")
def features():
    return render_template("features.html")


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=os.environ.get("FLASK_DEBUG") == "1")
