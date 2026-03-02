import os
from flask import Flask, render_template, jsonify, request
import psycopg2
from psycopg2.extras import RealDictCursor
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

# --- RAILWAY CONFIGURATION ---
# Railway provides DATABASE_URL. We use os.environ to get it securely.
DATABASE_URL = os.environ.get('DATABASE_URL')

# These will be set in the "Variables" tab on Railway
SENDER_EMAIL = os.environ.get('EMAIL_USER', 'vv708539@gmail.com')
SENDER_PASSWORD = os.environ.get('EMAIL_PASS', 'osjx pfrw sjtc cglf')
RECEIVER_EMAIL = os.environ.get('RECEIVER_EMAIL', 'krishnasurya2011@gmail.com')

def get_db_connection():
    # Railway's DATABASE_URL is a complete connection string
    return psycopg2.connect(DATABASE_URL)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/students')
def get_students():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    # Fetching names in the exact order for automatic display
    cur.execute("SELECT name, register_no, gender, category FROM students ORDER BY id ASC")
    students = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(students)

@app.route('/api/submit', methods=['POST'])
def submit_attendance():
    data = request.json
    date = data['date']
    records = data['records'] # List of students with marked status

    # Initialize counters for the report
    stats = {
        "total_p": 0, "total_a": 0,
        "ds_boys_p": 0, "h_boys_p": 0, "ds_boys_a": 0, "h_boys_a": 0,
        "ds_girls_p": 0, "h_girls_p": 0, "ds_girls_a": 0, "h_girls_a": 0,
        "absent_list": [], "od_list": []
    }

    for r in records:
        status = r['status']
        gender = r['gender'].lower()
        cat = r['category'].lower()

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

    # Construct the exact report format you requested
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

    # Send Email
    msg = MIMEText(report)
    msg['Subject'] = f"Attendance Report: {date}"
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)

    return jsonify({"status": "success"})

if __name__ == '__main__':
    # On Railway, the PORT is assigned dynamically
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)