import os
import csv
import smtplib
from flask import Flask, render_template, jsonify, request
from email.mime.text import MIMEText

app = Flask(__name__)

# --- CONFIGURATION ---
# Pulls from Render "Environment Variables"
SENDER_EMAIL = os.environ.get('EMAIL_USER', "vv708539@gmail.com")
SENDER_PASSWORD = os.environ.get('EMAIL_PASS', "osjx pfrw sjtc cglf")

# Fetches receiver emails from environment variable as a comma-separated list
# Example: "email1@gmail.com,email2@gmail.com"
raw_emails = os.environ.get('RECEIVER_EMAILS_LIST', "krishnasurya2011@gmail.com,msulthan139@gmail.com")
RECEIVER_EMAILS = [email.strip() for email in raw_emails.split(',')]

def load_students_from_csv():
    students = []
    try:
        # Looks for students.csv in your main folder
        base_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_path, 'students.csv')
        
        # 'utf-8-sig' handles hidden characters if the CSV was saved via Excel
        with open(file_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                students.append({
                    "name": row['name'].strip(),
                    "register_no": row['register_no'].strip(),
                    "gender": row['gender'].strip(),
                    "category": row['category'].strip()
                })
        print(f"Successfully loaded {len(students)} students.")
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
    date = data.get('date', 'Unknown Date')
    records = data.get('records', [])

    stats = {
        "total_p": 0, "total_a": 0,
        "ds_boys_a_count": 0, "ds_girls_a_count": 0,
        "h_boys_a_count": 0, "h_girls_a_count": 0,
        "ds_boys_list": [], "ds_girls_list": [],
        "h_boys_list": [], "h_girls_list": [],
        "od_list": []
    }

    # Process attendance records
    for r in records:
        status = r['status']
        gender = str(r.get('gender', '')).lower().strip()
        cat = str(r.get('category', '')).lower().strip()
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
            else: # female
                if 'day' in cat:
                    stats["ds_girls_a_count"] += 1
                    stats["ds_girls_list"].append(info)
                else:
                    stats["h_girls_a_count"] += 1
                    stats["h_girls_list"].append(info)
        elif status == 'OD':
            stats["od_list"].append(info)

    # Construct the Report String
    report = f"""
DAILY ATTENDANCE REPORT - {date}

Total Present: {stats['total_p']}
Total Absent: {stats['total_a']}

ABSENT SUMMARY:
Total Day Scholar boys: {stats['ds_boys_a_count']}
Total Day Scholar girls: {stats['ds_girls_a_count']}
Total Hosteller boys: {stats['h_boys_a_count']}
Total Hosteller girls: {stats['h_girls_a_count']}

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

    # Email Sending Logic
    try:
        print("Connecting to SMTP server...")
        # Use Port 587 + STARTTLS for better reliability on Render
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=30)
        server.starttls() 
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        
        for receiver in RECEIVER_EMAILS:
            msg = MIMEText(report)
            msg['Subject'] = f"Attendance Report: {date}"
            msg['From'] = SENDER_EMAIL
            msg['To'] = receiver
            server.send_message(msg)
            print(f"Email sent successfully to {receiver}")
        
        server.quit()
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"SMTP Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
