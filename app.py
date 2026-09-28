from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

from database import create_database

app = Flask(__name__)

# Secret key for session management
app.secret_key = "college_complaint_secret_key"


# Create database when application starts
create_database()


# Database connection function
def get_db_connection():
    connection = sqlite3.connect("complaints.db")
    connection.row_factory = sqlite3.Row
    return connection


# Home page
@app.route("/")
def index():
    return render_template("index.html")


# Student registration
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        connection = get_db_connection()

        try:
            connection.execute(
                """
                INSERT INTO students (name, email, password)
                VALUES (?, ?, ?)
                """,
                (name, email, password)
            )

            connection.commit()
            connection.close()

            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            connection.close()

            return render_template(
                "register.html",
                error="Email already registered."
            )

    return render_template("register.html")


# Student login
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        # Admin login
        if email == "admin@college.com" and password == "admin123":
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))

        connection = get_db_connection()

        student = connection.execute(
            """
            SELECT * FROM students
            WHERE email = ? AND password = ?
            """,
            (email, password)
        ).fetchone()

        connection.close()

        if student:

            session["student_id"] = student["id"]
            session["student_name"] = student["name"]

            return redirect(url_for("student_dashboard"))

        return render_template(
            "login.html",
            error="Invalid email or password."
        )

    return render_template("login.html")


# Student dashboard
@app.route("/student-dashboard")
def student_dashboard():

    if "student_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()

    complaints = connection.execute(
        """
        SELECT * FROM complaints
        WHERE student_id = ?
        ORDER BY created_at DESC
        """,
        (session["student_id"],)
    ).fetchall()

    connection.close()

    return render_template(
        "student_dashboard.html",
        complaints=complaints,
        student_name=session["student_name"]
    )


# Submit complaint
@app.route("/complaint", methods=["GET", "POST"])
def complaint():

    if "student_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        category = request.form["category"]
        title = request.form["title"]
        description = request.form["description"]

        connection = get_db_connection()

        connection.execute(
            """
            INSERT INTO complaints
            (student_id, category, title, description, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                session["student_id"],
                category,
                title,
                description,
                "Pending"
            )
        )

        connection.commit()
        connection.close()

        return redirect(url_for("student_dashboard"))

    return render_template("complaint.html")


# Admin dashboard
@app.route("/admin")
def admin_dashboard():

    if "admin" not in session:
        return redirect(url_for("login"))

    search = request.args.get("search", "")

    connection = get_db_connection()

    if search:

        complaints = connection.execute(
            """
            SELECT complaints.*, students.name, students.email
            FROM complaints
            JOIN students
            ON complaints.student_id = students.id
            WHERE complaints.title LIKE ?
               OR complaints.category LIKE ?
               OR complaints.status LIKE ?
               OR students.name LIKE ?
            ORDER BY complaints.created_at DESC
            """,
            (
                "%" + search + "%",
                "%" + search + "%",
                "%" + search + "%",
                "%" + search + "%"
            )
        ).fetchall()

    else:

        complaints = connection.execute(
            """
            SELECT complaints.*, students.name, students.email
            FROM complaints
            JOIN students
            ON complaints.student_id = students.id
            ORDER BY complaints.created_at DESC
            """
        ).fetchall()

    connection.close()

    return render_template(
        "admin_dashboard.html",
        complaints=complaints,
        search=search
    )


# Update complaint status
@app.route("/update-status/<int:complaint_id>", methods=["POST"])
def update_status(complaint_id):

    if "admin" not in session:
        return redirect(url_for("login"))

    status = request.form["status"]

    connection = get_db_connection()

    connection.execute(
        """
        UPDATE complaints
        SET status = ?
        WHERE id = ?
        """,
        (status, complaint_id)
    )

    connection.commit()
    connection.close()

    return redirect(url_for("admin_dashboard"))


# Logout
@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)