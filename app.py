import os
from flask import Flask, render_template, jsonify, request
import psycopg2
from psycopg2.extras import RealDictCursor
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

# --- DATABASE CONFIGURATION ---
# This automatically uses Render's database when deployed
DATABASE_URL = os.environ.get('DATABASE_URL', "postgresql://postgres:1234@localhost/classdb")

# --- EMAIL CONFIGURATION ---
SENDER_EMAIL = "vv708539@gmail.com"
SENDER_PASSWORD = "osjx pfrw sjtc cglf"

# Added three receiver mails as requested
RECEIVER_EMAILS = [
    "krishnasurya2011@gmail.com",
    "second_email@gmail.com", # Change these to your actual emails
    "third_email@gmail.com"
]

def get_db_connection():
    # If on Render, we need sslmode=require
    if "render.com" in DATABASE_URL or "dpg-" in DATABASE_URL:
        return psycopg2.connect(DATABASE_URL + "?sslmode=require")
    return psycopg2.connect(DATABASE_URL)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/students')
def get_students():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT name, register_no, gender, category FROM students ORDER BY id ASC")
        students = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(students)
    except Exception as e:
        print(f"Database Error: {e}")
        return jsonify([]), 500

@app.route('/api/submit', methods=['POST'])
def submit_attendance():
    data = request.json
    date = data['date']
    records = data['records']

    stats = {
        "total_p": 0, "total_a": 0,
        "ds_boys_p": 0, "h_boys_p": 0, "ds_boys_a": 0, "h_boys_a": 0,
        "ds_girls_p": 0, "h_girls_p": 0, "ds_girls_a": 0, "h_girls_a": 0,
        "absent_list": [], "od_list": []
    }

    for r in records:
        status = r['status']
        gender = r.get('gender', 'male').lower()
        cat = r.get('category', 'day_scholar').lower()

        if status == 'Present':
            stats["total_p"] += 1
            if gender == 'male':
                if cat == 'day_scholar': stats["ds_boys_p"] += 1
                else: stats["h_boys_p"] += 1
            else:
                if cat == 'day_scholar': stats["ds_girls_p"] += 1
                else: stats["h_girls_p"] += 1
        elif status == 'Absent':
            stats["total_a"] += 1
            stats["absent_list"].append(f"{r['name']} ({r['register_no']})")
            if gender == 'male':
                if cat == 'day_scholar': stats["ds_boys_a"] += 1
                else: stats["h_boys_a"] += 1
            else:
                if cat == 'day_scholar': stats["ds_girls_a"] += 1
                else: stats["h_girls_a"] += 1
        elif status == 'OD':
            stats["od_list"].append(f"{r['name']} ({r['register_no']})")

    report = f"""
DAILY ATTENDANCE REPORT - {date}

Total Present: {stats['total_p']}
Total Absent: {stats['total_a']}
Total Dayscoler boys present: {stats['ds_boys_p']}
Total hosteller boys present: {stats['h_boys_p']}
Total Dayscoler boys absent: {stats['ds_boys_a']}
Total hosteller boys absent: {stats['h_boys_a']}
Total Dayscoler girls present: {stats['ds_girls_p']}
Total hosteller girls present: {stats['h_girls_p']}
Total Dayscoler girls absent: {stats['ds_girls_a']}
Total hosteller girls absent: {stats['h_girls_a']}

OD Students:
{chr(10).join(stats['od_list']) if stats['od_list'] else 'None'}

Absent Students Names:
{chr(10).join(stats['absent_list']) if stats['absent_list'] else 'None'}
"""

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            for receiver in RECEIVER_EMAILS:
                msg = MIMEText(report)
                msg['Subject'] = f"Attendance Report: {date}"
                msg['From'] = SENDER_EMAIL
                msg['To'] = receiver
                server.send_message(msg)
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"Email Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
