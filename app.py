import os
import bcrypt
from flask import Flask, render_template, request, redirect, url_for, session, flash
import pymysql
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback_secret")

# Database connection helper
def get_db_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "registration"),
        cursorclass=pymysql.cursors.DictCursor
    )

# --- HOME ROUTE ---
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("todos"))
    return redirect(url_for("login"))

# --- REGISTER ROUTE ---
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Server-side validation rules
        if not name:
            flash("Name is required", "register_error")
            return render_template("register.html")
        if not email:
            flash("Email is required", "register_error")
            return render_template("register.html")
        if not password:
            flash("Password is required", "register_error")
            return render_template("register.html")
        if not confirm_password:
            flash("Confirm password is required", "register_error")
            return render_template("register.html")
        if password != confirm_password:
            flash("Passwords do not match", "register_error")
            return render_template("register.html")

        # Hash password securely using bcrypt
        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                sql = "INSERT INTO users (email, name, password_hash) VALUES (%s, %s, %s)"
                cursor.execute(sql, (email, name, password_hash))
                connection.commit()
                
                # Log user in after successful registration
                cursor.execute("SELECT user_id, name FROM users WHERE email = %s", (email,))
                user = cursor.fetchone()
                session["user_id"] = user["user_id"]
                session["user_name"] = user["name"]
                return redirect(url_for("todos"))
        except pymysql.err.IntegrityError:
            flash("Email Already Exists", "register_error")
            return render_template("register.html")
        finally:
            connection.close()

    return render_template("register.html")

# --- LOGIN ROUTE ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email:
            flash("Email is required", "login_error")
            return render_template("login.html")
        if not password:
            flash("Password is required", "login_error")
            return render_template("login.html")

        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT user_id, name, password_hash FROM users WHERE email = %s", (email,))
                user = cursor.fetchone()

                # Verify password against hash
                if user and bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
                    session["user_id"] = user["user_id"]
                    session["user_name"] = user["name"]
                    return redirect(url_for("todos"))
                else:
                    flash("Invalid email or password", "login_error")
                    return render_template("login.html")
        finally:
            connection.close()

    return render_template("login.html")

# --- LOGOUT ROUTE ---
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# --- TODOS DASHBOARD ROUTE ---
@app.route("/todos", methods=["GET", "POST"])
def todos():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    connection = get_db_connection()

    if request.method == "POST":
        action = request.form.get("action")

        # ADD TO-DO
        if action == "add":
            title = request.form.get("title", "").strip()
            if not title:
                flash("Title is required (an empty title or only spaces)", "todo_error")
            elif len(title) > 200:
                flash("Title is too long (200 characters at most)", "todo_error")
            else:
                with connection.cursor() as cursor:
                    sql = "INSERT INTO todos (user_id, title) VALUES (%s, %s)"
                    cursor.execute(sql, (user_id, title))
                    connection.commit()

        # EDIT TITLE
        elif action == "edit":
            todo_id = request.form.get("todo_id")
            title = request.form.get("title", "").strip()
            if not title:
                flash("Title is required (an empty title or only spaces)", "todo_error")
            elif len(title) > 200:
                flash("Title is too long (200 characters at most)", "todo_error")
            else:
                with connection.cursor() as cursor:
                    sql = "UPDATE todos SET title = %s WHERE todo_id = %s AND user_id = %s"
                    cursor.execute(sql, (title, todo_id, user_id))
                    connection.commit()

        # MARK DONE / NOT DONE
        elif action == "toggle":
            todo_id = request.form.get("todo_id")
            is_done = 1 if request.form.get("is_done") == "1" else 0
            with connection.cursor() as cursor:
                sql = "UPDATE todos SET is_done = %s WHERE todo_id = %s AND user_id = %s"
                cursor.execute(sql, (is_done, todo_id, user_id))
                connection.commit()

        # DELETE TO-DO
        elif action == "delete":
            todo_id = request.form.get("todo_id")
            with connection.cursor() as cursor:
                sql = "DELETE FROM todos WHERE todo_id = %s AND user_id = %s"
                cursor.execute(sql, (todo_id, user_id))
                connection.commit()

        connection.close()
        return redirect(url_for("todos"))

    # Fetch user's to-dos (newest first)
    with connection.cursor() as cursor:
        cursor.execute("SELECT todo_id, title, is_done, created_at FROM todos WHERE user_id = %s ORDER BY todo_id DESC", (user_id,))
        todo_list = cursor.fetchall()
    connection.close()

    return render_template("todos.html", todos=todo_list, name=session.get("user_name"))

if __name__ == "__main__":
    app.run(debug=True)