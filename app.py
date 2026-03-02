import os
import csv
import smtplib
from flask import Flask, render_template, jsonify, request
from email.mime.text import MIMEText

app = Flask(__name__)

# --- CONFIGURATION ---
# These pull from your Render "Environment Variables"
SENDER_EMAIL = os.environ.get('EMAIL_USER', "vv708539@gmail.com")
SENDER_PASSWORD = os.environ.get('EMAIL_PASS', "osjx pfrw sjtc cglf")

RECEIVER_EMAILS = [
    "krishnasurya2011@gmail.com",
    "msulthan139@gmail.com", 
    "third_email@example.com"
]

def load_students_from_csv():
    students = []
    try:
        # This looks for students.csv in your main folder
        file_path = os.path.join(os.path.dirname(__file__), 'students.csv')
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                students.append({
                    "name": row['name'],
                    "register_no": row['register_no'],
                    "gender": row['gender'],
                    "category": row['category']
                })
    except Exception as e:
        print(f"CSV Error: {e}")
    return students

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/students')
def get_students():
    students = load_students_from_csv()
    if not students:
        return jsonify({"error": "No students found in CSV"}), 404
    return jsonify(students)

@app.route('/api/submit', methods=['POST'])
def submit_attendance():
    data = request.json
    date = data['date']
    records = data['records']

    stats = {
        "total_p": 0, "total_a": 0,
        "ds_boys_a_count": 0, "ds_girls_a_count": 0,
        "h_boys_a_count": 0, "h_girls_a_count": 0,
        "ds_boys_list": [], "ds_girls_list": [],
        "h_boys_list": [], "h_girls_list": [],
        "od_list": []
    }

    for r in records:
        status = r['status']
        gender = str(r.get('gender', '')).lower()
        cat = str(r.get('category', '')).lower()
        info = f"{r['name']} ({r['register_no']})"

        if status == 'Present':
            stats["total_p"] += 1
        elif status == 'Absent':
            stats["total_a"] += 1
            if gender == 'male':
                if 'day' in cat:
                    stats["ds_boys_a_count"] += 1
                    stats["ds_boys_list"].append(info)
                else:
                    stats["h_boys_a_count"] += 1
                    stats["h_boys_list"].append(info)
            else:
                if 'day' in cat:
                    stats["ds_girls_a_count"] += 1
                    stats["ds_girls_list"].append(info)
                else:
                    stats["h_girls_a_count"] += 1
                    stats["h_girls_list"].append(info)
        elif status == 'OD':
            stats["od_list"].append(info)

    report = f"""
DAILY ATTENDANCE REPORT - {date}

Total Present: {stats['total_p']}
Total Absent: {stats['total_a']}

ABSENT SUMMARY:
Total Dayscoler boys: {stats['ds_boys_a_count']}
Total Dayscoler girls: {stats['ds_girls_a_count']}
Total hosteller boys: {stats['h_boys_a_count']}
Total hosteller girls: {stats['h_girls_a_count']}

DETAILED ABSENT LIST:

[Day Scholar Boys]
{"\n".join(stats['ds_boys_list']) if stats['ds_boys_list'] else 'None'}

[Day Scholar Girls]
{"\n".join(stats['ds_girls_list']) if stats['ds_girls_list'] else 'None'}

[Hosteller Boys]
{"\n".join(stats['h_boys_list']) if stats['h_boys_list'] else 'None'}

[Hosteller Girls]
{"\n".join(stats['h_girls_list']) if stats['h_girls_list'] else 'None'}

OD Students:
{"\n".join(stats['od_list']) if stats['od_list'] else 'None'}
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
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)


