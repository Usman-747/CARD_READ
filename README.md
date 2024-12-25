# QR-Based Attendance Management System

## Overview
A robust and efficient QR-based attendance management system designed to simplify attendance tracking and reporting. Built using Flask, this system integrates secure login functionality, CSV export for attendance records, and a relational database to handle sessions, users, and attendance data.

The live site is hosted at: [saadkarim754.pythonanywhere.com](https://saadkarim754.pythonanywhere.com)

---

## Features

### Core Features:
- **User Authentication:** Secure login system to ensure only authorized access.
- **QR-Based Attendance:** Efficient attendance marking using QR codes.
- **Dynamic CSV Export:** Export filtered attendance records as CSV files based on session details.
- **Relational Database:** Centralized storage of users, sessions, and attendance records using SQLite.

### Filtering and Reporting:
- Filter attendance by date, semester, slot, subject, and type.
- Customize CSV filenames based on session attributes (e.g., `session_id-slot-semester-class-subject.csv`).
- Export attendance with additional user details (user ID and name).

---

## Installation

### Prerequisites:
- Python 3.7+
- pip (Python package installer)

### Steps:
1. Clone the repository:
   ```bash
   git clone https://github.com/saadkarim754/qr-attendance-system.git
   cd qr-attendance-system
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up the database:
   - Create the database schema using the provided SQL scripts or models in the app.
4. Run the Flask application:
   ```bash
   flask run
   ```
5. Access the application in your browser at `http://127.0.0.1:5000`.

---

## Usage

### Mark Attendance:
1. Log in with your credentials.
2. Navigate to the session you want to mark attendance for.
3. Use the QR scanner to register attendance.

### Export Attendance:
1. Access the CSV export settings.
2. Filter by date, semester, slot, subject, and attendance type.
3. Download the CSV file with session and user details.

---

## Database Schema

### Tables:
1. **Users:** Stores user details (ID, name, etc.).
2. **Sessions:** Stores session details (ID, semester, slot, subject, type).
3. **Attendance:** Links users and sessions with timestamps for when attendance was marked.

---

## Hosted Application
The live version of the application is available at: [saadkarim754.pythonanywhere.com](https://saadkarim754.pythonanywhere.com)

---

## Contributions
Contributions are welcome! Feel free to fork the repository and submit pull requests.

---

## License
This project is licensed under the MIT License. See the LICENSE file for details.
