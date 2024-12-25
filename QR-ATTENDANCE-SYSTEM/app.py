import os
import json
import qrcode
from io import BytesIO, StringIO
import csv
from cs50 import SQL
from werkzeug.utils import secure_filename
from flask import Flask, flash, redirect, render_template, request, session, send_file, url_for
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
from helpers import apology

# Configure application
app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///class-attendance.db")

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for("login"))
        user_id = session.get("user_id")
        user = db.execute("SELECT * FROM admins WHERE user_id = ?", user_id)
        if not user:
            flash("Admin privileges required.")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
def index():
    # Check if the user is logged in
    if session.get("user_id"):
        # Retrieve user details from the database
        rows = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])

        # Ensure the user exists in the database
        if len(rows) == 1:
            session["username"] = rows[0]["username"]

            # Check if the user is an admin by querying the admins table
            admin_check = db.execute("SELECT * FROM admins WHERE user_id = ?", session["user_id"])

            # If user is found in the admins table, mark them as an admin
            if admin_check:
                session["is_admin"] = True
            else:
                session["is_admin"] = False
        else:
            # If user data is missing, clear session and redirect to login
            session.clear()
            return redirect("/login")

    # Render the index page
    return render_template("index.html")



@app.route("/login", methods=["GET", "POST"])
def login():
    # Clear any existing session
    session.clear()

    if request.method == "POST":
        # Get email and password from the form
        email = request.form.get("email")
        password = request.form.get("password")

        # Check if inputs are provided
        if not email or not password:
            return render_template("apology.html", message="Must provide email and password", code=400)

        # Query the database for the user using email
        rows = db.execute("SELECT * FROM users WHERE email = ?", email)

        # Verify user exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            return render_template("apology.html", message="Invalid email and/or password", code=400)

        # Log the user in
        session["user_id"] = rows[0]["id"]
        session["username"] = rows[0]["username"]

        # Check if the user is an admin
        session["is_admin"] = rows[0].get("is_admin", False)

        # Redirect to index/dashboard
        return redirect("/")

    # If GET, render the login page
    return render_template("login.html")




@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Collect form data
        username = request.form.get("username")
        email = request.form.get("email")
        phone_number = request.form.get("phone_number")
        department = request.form.get("department")
        semester = request.form.get("semester")
        university_registration_number = request.form.get("university_registration_number")
        gender = request.form.get("gender")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Validate form data
        if not all([username, email, phone_number, department, semester, university_registration_number, gender, password, confirmation]):
            flash("All fields are required.", "danger")
            return redirect("/register")
        if password != confirmation:
            flash("Passwords do not match.", "danger")
            return redirect("/register")
        if len(password) <= 7:
            flash("Password must be at least 8 characters long.", "danger")
            return redirect("/register")
        if not semester.isdigit() or int(semester) <= 0:
            flash("Semester must be a positive number.", "danger")
            return redirect("/register")

        # Check for existing user
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        if rows:
            flash("Username already taken.", "danger")
            return redirect("/register")
        rows = db.execute("SELECT * FROM users WHERE email = ?", email)
        if rows:
            flash("Email already taken.", "danger")
            return redirect("/register")

        # Hash password
        hashh = generate_password_hash(password)

        # Insert new user into the database
        user_id = db.execute("""
            INSERT INTO users (username, email, phone_number, department, semester, university_registration_number, gender, hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, username, email, phone_number, department, semester, university_registration_number, gender, hashh)

        # Log the user in
        session["user_id"] = user_id
        session["username"] = username

        flash("Registered successfully!", "success")
        return redirect("/")
    return render_template("register.html")


@app.route("/admins")
@login_required
@admin_required
def admins():
    # Fetch all sessions created by the admin
    sessions = db.execute("""
        SELECT id, date, semester, slot, subject, attendance_type
        FROM sessions
        WHERE created_by = ?
        ORDER BY date DESC
    """, session["user_id"])

    # Fetch all attendance records for review
    attendance = db.execute("""
        SELECT attendance.id, users.username, sessions.date, sessions.subject, sessions.attendance_type
        FROM attendance
        JOIN users ON attendance.user_id = users.id
        JOIN sessions ON attendance.session_id = sessions.id
        ORDER BY sessions.date DESC
    """)

    return render_template("admins.html", sessions=sessions, attendance=attendance)


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user_id = session['user_id']
    user = db.execute("SELECT * FROM users WHERE id = ?", user_id)

    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('index'))

    user = user[0]  # Extract the first (and only) user data from the result

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        phone_number = request.form.get('phone_number')
        department = request.form.get('department')
        gender = request.form.get('gender')

        # Validate user input (you can add more validations if needed)
        if not username or not email:
            flash('Username and email are required!', 'danger')
            return redirect(url_for('profile'))

        # Update the user's information in the database
        db.execute("""
            UPDATE users
            SET username = ?, email = ?, phone_number = ?, department = ?, gender = ?
            WHERE id = ?
        """, username, email, phone_number, department, gender, user_id)

        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))

    return render_template('profile.html', user=user)



@app.route("/manage_attendance", methods=["GET", "POST"])
@login_required
def manage_attendance():
    # Get all unique subjects from the database
    subjects = db.execute("SELECT DISTINCT subject FROM sessions")

    if request.method == "POST":
        # Get the selected subject from the form
        selected_subject = request.form.get("subject")

        if not selected_subject:
            flash("Please select a subject.", "danger")
            return redirect("/manage_attendance")

        # Fetch attendance data for the selected subject
        attendance_data = db.execute("""
            SELECT users.username, sessions.date, sessions.slot, attendance.marked_on
            FROM attendance
            JOIN users ON attendance.user_id = users.id
            JOIN sessions ON attendance.session_id = sessions.id
            WHERE sessions.subject = ?
        """, selected_subject)

        return render_template("manage_attendance.html", subjects=subjects, attendance_data=attendance_data, selected_subject=selected_subject)

    return render_template("manage_attendance.html", subjects=subjects)








@app.route("/generate_qr", methods=["GET", "POST"])
@login_required
@admin_required  # Ensure that only admins can access this route
def generate_qr():
    # Enable foreign key enforcement
    db.execute("PRAGMA foreign_keys = ON;")

    try:
        if request.method == "POST":
            date = request.form.get("date")
            semester = request.form.get("semester")
            slot = request.form.get("slot")
            subject = request.form.get("subject")
            attendance_type = request.form.get("attendance_type")

            # Validate the form fields
            if not date or not semester or not slot or not subject or not attendance_type:
                flash("All fields are required!", "danger")
                return redirect("/generate_qr")

            # Insert session into the sessions table with a default created_by value (e.g., 0)
            session_id = db.execute("""
                INSERT INTO sessions (date, semester, slot, subject, attendance_type, created_by)
                VALUES (?, ?, ?, ?, ?, ?)
            """, date, semester, slot, subject, attendance_type, 1)  # Using 0 as the default value for created_by

            # Generate QR code with session details
            data = f"{date},{semester},{slot},{subject},{attendance_type}"
            qr = qrcode.QRCode()
            qr.add_data(data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer)
            buffer.seek(0)

            # Return the generated QR code as an image file
            return send_file(buffer, mimetype="image/png", as_attachment=True, download_name="attendance_qr.png")

    finally:
        # Disable foreign key enforcement
        db.execute("PRAGMA foreign_keys = OFF;")

    return render_template("generate_qr.html")



@app.route('/scan_qr', methods=['POST'])
def scan_qr():
    if 'user_id' not in session:
        flash("You need to be logged in to mark attendance.", "danger")
        return redirect("/login")

    user_id = session['user_id']
    qr_data = request.form.get('qr_data')

    if not qr_data:
        flash("No QR code data found.", "danger")
        return redirect("/")

    # Debugging: Print the QR data to the console
    print("QR Data received:", qr_data)

    # Assuming QR data is a comma-separated string with the required fields
    try:
        date, semester, slot, subject, attendance_type = qr_data.split(',')
        print("Parsed QR Info:", date, semester, slot, subject, attendance_type)  # Debugging: Print the parsed QR info
    except ValueError as e:
        print("Error parsing QR data:", e)  # Debugging: Print the error
        flash("Invalid QR code data.", "danger")
        return redirect("/")

    # Fetch the session ID based on QR code data
    session_data = db.execute("""
        SELECT id FROM sessions
        WHERE date = ? AND semester = ? AND slot = ? AND subject = ? AND attendance_type = ?
    """, (date),(semester),(slot),(subject),(attendance_type))

    if not session_data:
        flash("Invalid session data.", "danger")
        return redirect("/")

    session_id = session_data[0]["id"]

    # Insert the attendance record into the database
    db.execute("INSERT INTO attendance (user_id, session_id) VALUES (?, ?)", (user_id),(session_id))

    flash("Attendance marked successfully!", "success")
    return redirect("/")







@app.route('/show_attendance_csv_settings', methods=['GET', 'POST'])
@login_required
@admin_required
def show_attendance_csv_settings():
    if request.method == 'POST':
        date = request.form.get('date')
        semester = request.form.get('semester')
        slot = request.form.get('slot')
        subject = request.form.get('subject')
        attendance_type = request.form.get('attendance_type')

        # Redirect to download filtered attendance CSV with parameters
        return redirect(url_for('download_filtered_attendance_csv',
                                date=date,
                                semester=semester,
                                slot=slot,
                                subject=subject,
                                attendance_type=attendance_type))

    return render_template('show_attendance_csv_settings.html')


@app.route('/download_filtered_attendance_csv', methods=['POST'])
@login_required
def download_filtered_attendance_csv():
    date = request.form.get('date')
    semester = request.form.get('semester')
    slot = request.form.get('slot')
    subject = request.form.get('subject')
    attendance_type = request.form.get('attendance_type')

    if not all([date, semester, slot, subject, attendance_type]):
        flash("All fields are required.", "danger")
        return redirect("/show_attendance_csv_settings")

    try:
        # Debug: Print filter parameters
        print("Filter parameters:", (date), (semester), (slot), (subject), (attendance_type))

        # Fetch filtered attendance data including user name
        attendance_data = db.execute("""
            SELECT attendance.user_id,
                   (SELECT username FROM users WHERE users.id = attendance.user_id) AS user_name,
                   attendance.session_id,
                   attendance.marked_on,
                   sessions.semester,
                   sessions.slot,
                   sessions.subject,
                   sessions.attendance_type
            FROM attendance
            JOIN sessions ON attendance.session_id = sessions.id
            WHERE DATE(attendance.marked_on) = ?
              AND sessions.semester = ?
              AND sessions.slot = ?
              AND sessions.subject = ?
              AND sessions.attendance_type = ?
        """, (date), (semester), (slot), (subject), (attendance_type))  # Enclose values in round brackets

        # Debug: Print fetched data
        print("Attendance Data:", (attendance_data))

        if not attendance_data:
            flash("No matching records found.", "danger")
            return redirect("/show_attendance_csv_settings")

        # Dynamically name the CSV file based on session details
        session_info = attendance_data[0]  # Assume at least one record exists
        csv_filename = f"{session_info['session_id']}-{session_info['slot']}-{session_info['semester']}-class-{session_info['subject']}.csv"

        # Create CSV file in StringIO
        output = StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

        # Write header
        writer.writerow(['User ID', 'User Name', 'Session ID', 'Marked On', 'Semester', 'Slot', 'Subject', 'Attendance Type'])

        # Write rows
        for row in attendance_data:
            writer.writerow([
                (row['user_id']), (row['user_name']), (row['session_id']), (row['marked_on']),
                (row['semester']), (row['slot']), (row['subject']), (row['attendance_type'])
            ])

        # Convert StringIO to BytesIO
        byte_output = BytesIO(output.getvalue().encode('utf-8'))
        output.close()

        # Return as downloadable file
        return send_file(byte_output,
                         mimetype='text/csv',
                         as_attachment=True,
                         download_name=csv_filename)

    except Exception as e:
        print("SQL Query Error:", (e))  # Debug: Print error details enclosed in brackets
        flash("Error fetching attendance data.", "danger")
        return redirect("/show_attendance_csv_settings")


if __name__ == "__main__":
    app.run(debug=True)
