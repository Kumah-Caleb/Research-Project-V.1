from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from flask_cors import CORS
from functools import wraps
import os
import json
import hashlib
import secrets
from datetime import datetime, timedelta
import uuid

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
CORS(app)

# Data file paths
USERS_FILE = 'data/users.json'
COURSES_FILE = 'data/courses.json'
ENROLLMENTS_FILE = 'data/enrollments.json'
PREDICTIONS_FILE = 'data/predictions.json'
WEEKLY_DATA_FILE = 'data/weekly_data.json'
SEMESTER_DATA_FILE = 'data/semester_data.json'
CUSTOM_PREDICTIONS_FILE = 'data/custom_predictions.json'

# Ghanaian University Academic Calendar Configuration
class GhanaUniversityCalendar:
    def __init__(self):
        # 2024/2025 Academic Calendar (Ghanaian University System)
        self.first_semester_start = datetime(2024, 8, 26)    # Late August
        self.first_semester_end = datetime(2024, 12, 13)     # Mid December
        self.second_semester_start = datetime(2025, 1, 13)   # Mid January
        self.second_semester_end = datetime(2025, 4, 25)     # Late April
        self.special_semester_start = datetime(2025, 5, 5)   # May (Non-Regular)
        self.special_semester_end = datetime(2025, 7, 25)    # July
        
        # Regular: 5 days/week (Mon-Fri), Non-Regular: Weekends/Saturdays
        self.regular_lecture_days_per_week = 5
        self.non_regular_lecture_days_per_week = 2  # Saturdays + some Sundays
        
        # Total weeks per semester
        self.weeks_per_semester = 15
        
    def get_current_program_type(self, user_role='regular'):
        """Determine if user is Regular or Non-Regular based on their program"""
        today = datetime.now()
        
        if user_role == 'regular':
            if today < self.first_semester_end:
                return 'Regular - First Semester'
            elif today < self.second_semester_end:
                return 'Regular - Second Semester'
        else:  # non-regular
            if self.special_semester_start <= today <= self.special_semester_end:
                return 'Non-Regular - Special Semester'
            # Non-regular also can be in regular semesters (evening/weekend programs)
            elif today < self.first_semester_end:
                return 'Non-Regular - First Semester (Weekend/Evening)'
            elif today < self.second_semester_end:
                return 'Non-Regular - Second Semester (Weekend/Evening)'
        
        return 'Semester Break'
    
    def get_current_week(self, program_type='regular'):
        """Calculate current week based on program type"""
        today = datetime.now()
        
        if program_type == 'regular':
            if today < self.first_semester_end:
                delta = today - self.first_semester_start
            elif today < self.second_semester_end:
                delta = today - self.second_semester_start
            else:
                return 0
        else:  # non-regular
            if today < self.first_semester_end:
                delta = today - self.first_semester_start
            elif today < self.second_semester_end:
                delta = today - self.second_semester_start
            elif self.special_semester_start <= today <= self.special_semester_end:
                delta = today - self.special_semester_start
            else:
                return 0
        
        week = (delta.days // 7) + 1
        return min(max(week, 1), self.weeks_per_semester)
    
    def get_weeks_remaining(self, program_type='regular'):
        current_week = self.get_current_week(program_type)
        if current_week == 0:
            return 0
        return self.weeks_per_semester - current_week
    
    def get_total_lecture_hours(self, program_type='regular', credit_hours=3):
        """
        Calculate total lecture hours per semester
        - Regular: 5 days/week × 15 weeks = 75 days × 3 hours = 225 hours
        - Non-Regular: 2 days/week × 15 weeks = 30 days × 3 hours = 90 hours
        """
        if program_type == 'regular':
            total_days = self.regular_lecture_days_per_week * self.weeks_per_semester
        else:
            total_days = self.non_regular_lecture_days_per_week * self.weeks_per_semester
        
        return total_days * credit_hours
    
    def get_lectures_conducted(self, program_type='regular', weeks_completed=1):
        """Get lectures conducted so far"""
        days_per_week = self.regular_lecture_days_per_week if program_type == 'regular' else self.non_regular_lecture_days_per_week
        return days_per_week * weeks_completed * 3  # 3 hours per lecture day

calendar = GhanaUniversityCalendar()

def init_data_files():
    """Initialize data files"""
    os.makedirs('data', exist_ok=True)
    for file in [USERS_FILE, COURSES_FILE, ENROLLMENTS_FILE, PREDICTIONS_FILE, 
                 WEEKLY_DATA_FILE, SEMESTER_DATA_FILE, CUSTOM_PREDICTIONS_FILE]:
        if not os.path.exists(file):
            with open(file, 'w') as f:
                json.dump({}, f)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_data(file):
    with open(file, 'r') as f:
        return json.load(f)

def save_data(file, data):
    with open(file, 'w') as f:
        json.dump(data, f, indent=2)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

def lecturer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'lecturer':
            flash('Access denied. Lecturer privileges required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

init_data_files()

# ============ PREDICTION ENGINE WITH GHANAIAN UNIVERSITY SYSTEM ============

def calculate_semester_prediction(data):
    """Calculate prediction based on semester data with Regular/Non-Regular support"""
    program_type = data.get('program_type', 'regular')
    credit_hours = data.get('credit_hours', 3)
    
    # Total possible lectures based on program type
    total_lectures = calendar.get_total_lecture_hours(program_type, credit_hours)
    lectures_attended = data.get('lectures_attended', 0)
    
    # Attendance percentage
    attendance_percentage = (lectures_attended / total_lectures * 100) if total_lectures > 0 else 0
    attendance_percentage = min(100, attendance_percentage)
    
    # Assignments calculation
    total_assignments = data.get('total_assignments', 0)
    assignments_completed = data.get('assignments_completed', 0)
    assignments_score = data.get('assignments_score', 0)  # Average score per assignment
    
    assignment_completion_rate = (assignments_completed / total_assignments * 100) if total_assignments > 0 else 0
    
    # Engagement calculation
    total_engagements = data.get('total_engagements', 0)
    engagements_participated = data.get('engagements_participated', 0)
    engagement_rate = (engagements_participated / total_engagements * 100) if total_engagements > 0 else 0
    
    # Weighted score calculation
    weighted_score = (
        attendance_percentage * 0.25 +
        assignment_completion_rate * 0.15 +
        assignments_score * 0.20 +
        engagement_rate * 0.15 +
        data.get('study_hours', 0) / 20 * 100 * 0.15 +
        data.get('previous_grade', 0) * 0.10
    )
    
    return weighted_score, {
        'attendance_percentage': attendance_percentage,
        'assignment_completion': assignment_completion_rate,
        'assignments_quality': assignments_score,
        'engagement_rate': engagement_rate,
        'total_lectures': total_lectures,
        'lectures_attended': lectures_attended
    }

def calculate_weekly_prediction(data):
    """Calculate prediction based on weekly data"""
    program_type = data.get('program_type', 'regular')
    weeks_completed = data.get('weeks_completed', 1)
    total_weeks = calendar.weeks_per_semester
    
    # Average weekly performance
    avg_attendance = data.get('weekly_attendance', 0)
    avg_assignments = data.get('weekly_assignments', 0)
    avg_engagement = data.get('weekly_engagement', 0)
    avg_study_hours = data.get('weekly_study_hours', 0)
    
    # Projected final performance
    projected_score = (
        avg_attendance * 0.25 +
        avg_assignments * 0.25 +
        avg_engagement * 0.20 +
        (avg_study_hours / 20 * 100) * 0.20 +
        data.get('midterm_grade', 0) * 0.10
    )
    
    weeks_remaining = total_weeks - weeks_completed
    if weeks_remaining > 0 and projected_score < 70:
        projected_score += (100 - projected_score) * (weeks_remaining / total_weeks) * 0.3
    
    return projected_score

def calculate_custom_prediction(data):
    """Calculate prediction based on custom user-defined metrics"""
    weights = data.get('weights', {
        'attendance': 0.25,
        'assignments': 0.25,
        'engagement': 0.20,
        'study_hours': 0.15,
        'previous_grade': 0.15
    })
    
    total = sum(weights.values())
    if total > 0:
        weights = {k: v/total for k, v in weights.items()}
    
    weighted_score = (
        data.get('attendance', 0) * weights.get('attendance', 0.25) +
        data.get('assignments', 0) * weights.get('assignments', 0.25) +
        data.get('engagement', 0) * weights.get('engagement', 0.20) +
        (data.get('study_hours', 0) / 20 * 100) * weights.get('study_hours', 0.15) +
        data.get('previous_grade', 0) * weights.get('previous_grade', 0.15)
    )
    
    return weighted_score

def get_prediction_grade(score):
    """AAMUSTED Grading System"""
    if score >= 85:
        return "A - Excellent", score
    elif score >= 80:
        return "B+ - Very Good", score
    elif score >= 75:
        return "B - Good", score
    elif score >= 70:
        return "C+ - Above Average", score
    elif score >= 65:
        return "C - Average", score
    elif score >= 60:
        return "D+ - Below Average", score
    elif score >= 55:
        return "D - Pass", score
    else:
        return "F - Fail", score

def generate_recommendations(data, score, metrics):
    """Generate personalized recommendations"""
    recommendations = []
    program_type = data.get('program_type', 'regular')
    program_name = "Regular" if program_type == 'regular' else "Non-Regular (Weekend/Evening)"
    
    recommendations.append(f"📚 Program Type: {program_name}")
    
    # Attendance recommendations
    if metrics['attendance_percentage'] < 70:
        lectures_needed = (metrics['total_lectures'] * 0.85) - metrics['lectures_attended']
        if lectures_needed > 0:
            recommendations.append(f"📅 Attendance: {metrics['attendance_percentage']:.0f}% ({metrics['lectures_attended']}/{metrics['total_lectures']} hours). Need {lectures_needed:.0f} more hours to reach 85%")
    elif metrics['attendance_percentage'] >= 85:
        recommendations.append(f"✅ Excellent attendance: {metrics['attendance_percentage']:.0f}%")
    
    # Assignment recommendations
    if metrics['assignment_completion'] < 70:
        recommendations.append(f"📝 Assignment completion: {metrics['assignment_completion']:.0f}%. Complete all pending assignments")
    
    if metrics['assignments_quality'] < 65:
        recommendations.append(f"✍️ Assignment quality: {metrics['assignments_quality']:.0f}%. Review feedback and improve")
    
    # Engagement recommendations
    if metrics['engagement_rate'] < 60:
        recommendations.append(f"💬 Class engagement: {metrics['engagement_rate']:.0f}%. Participate more in discussions")
    
    # Study hours recommendations
    study_hours = data.get('study_hours', 0)
    if program_type == 'regular':
        target_hours = 15
    else:
        target_hours = 12  # Non-regular students have less time
    
    if study_hours < target_hours:
        recommendations.append(f"⏰ Study hours: {study_hours} hrs/week. Target {target_hours} hours for {program_name} program")
    
    weeks_remaining = calendar.get_weeks_remaining(program_type)
    if weeks_remaining > 0 and score < 70:
        recommendations.append(f"📊 {weeks_remaining} weeks remaining. Create a weekly study plan")
    
    if score >= 85:
        recommendations.append("🌟 Excellent performance! Keep up the great work")
    elif score >= 70:
        recommendations.append("👍 Good progress! Focus on weaker areas")
    elif score >= 55:
        recommendations.append("⚠️ At risk level. Seek academic support immediately")
    else:
        recommendations.append("🆘 Critical intervention needed. Contact academic advisor")
    
    return recommendations

# ============ PAGE ROUTES ============

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('landing.html', calendar=calendar)

@app.route('/login')
def login_page():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/register')
def register_page():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    program_type = session.get('program_type', 'regular')
    current_week = calendar.get_current_week(program_type)
    weeks_remaining = calendar.get_weeks_remaining(program_type)
    
    if session.get('role') == 'lecturer':
        return render_template('lecturer_dashboard.html', user=session, calendar=calendar, 
                               current_week=current_week, weeks_remaining=weeks_remaining)
    return render_template('student_dashboard.html', user=session, calendar=calendar,
                          current_week=current_week, weeks_remaining=weeks_remaining)

@app.route('/predictor')
@login_required
def predictor():
    courses = []
    if session.get('role') == 'student':
        enrollments = load_data(ENROLLMENTS_FILE)
        user_enrollments = enrollments.get(session['user_id'], [])
        all_courses = load_data(COURSES_FILE)
        courses = [all_courses[cid] for cid in user_enrollments if cid in all_courses]
    return render_template('predictor.html', user=session, courses=courses, calendar=calendar)

@app.route('/semester')
@login_required
def semester():
    return render_template('semester.html', user=session, calendar=calendar)

@app.route('/weekly')
@login_required
def weekly():
    current_week = calendar.get_current_week(session.get('program_type', 'regular'))
    return render_template('weekly.html', user=session, calendar=calendar, current_week=current_week)

@app.route('/custom')
@login_required
def custom():
    return render_template('custom.html', user=session)

@app.route('/history')
@login_required
def history():
    predictions = load_data(PREDICTIONS_FILE)
    custom_predictions = load_data(CUSTOM_PREDICTIONS_FILE)
    user_predictions = predictions.get(session['user_id'], [])
    user_custom = custom_predictions.get(session['user_id'], [])
    return render_template('history.html', user=session, predictions=user_predictions, custom=user_custom)

@app.route('/courses')
@login_required
def courses():
    all_courses = load_data(COURSES_FILE)
    enrollments = load_data(ENROLLMENTS_FILE)
    user_enrollments = enrollments.get(session['user_id'], [])
    return render_template('courses.html', user=session, courses=all_courses, enrolled=user_enrollments)

@app.route('/students')
@lecturer_required
def students():
    users = load_data(USERS_FILE)
    student_list = [u for u in users.values() if u.get('role') == 'student']
    courses = load_data(COURSES_FILE)
    enrollments = load_data(ENROLLMENTS_FILE)
    predictions = load_data(PREDICTIONS_FILE)
    return render_template('students.html', students=student_list, courses=courses, 
                          enrollments=enrollments, predictions=predictions, user=session,
                          calendar=calendar)

# ============ API ENDPOINTS ============

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.json
    users = load_data(USERS_FILE)
    
    if data['username'] in users:
        return jsonify({'success': False, 'error': 'Username exists'}), 400
    
    for user in users.values():
        if user.get('email') == data['email']:
            return jsonify({'success': False, 'error': 'Email registered'}), 400
    
    user_id = str(uuid.uuid4())[:8]
    users[user_id] = {
        'id': user_id,
        'username': data['username'],
        'email': data['email'],
        'password': hash_password(data['password']),
        'role': data.get('role', 'student'),
        'full_name': data['full_name'],
        'index_number': data.get('index_number', ''),
        'program_type': data.get('program_type', 'regular'),
        'department': data.get('department', ''),
        'level': data.get('level', '100'),
        'created_at': datetime.now().isoformat()
    }
    
    save_data(USERS_FILE, users)
    session['user_id'] = user_id
    session['username'] = data['username']
    session['role'] = data.get('role', 'student')
    session['full_name'] = data['full_name']
    session['index_number'] = data.get('index_number', '')
    session['program_type'] = data.get('program_type', 'regular')
    
    return jsonify({'success': True, 'role': session['role']})

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    users = load_data(USERS_FILE)
    
    for user_id, user in users.items():
        if user['username'] == data['username'] and user['password'] == hash_password(data['password']):
            session['user_id'] = user_id
            session['username'] = user['username']
            session['role'] = user['role']
            session['full_name'] = user['full_name']
            session['index_number'] = user.get('index_number', '')
            session['program_type'] = user.get('program_type', 'regular')
            return jsonify({'success': True, 'role': user['role']})
    
    return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/courses', methods=['GET', 'POST'])
@login_required
def manage_courses():
    courses = load_data(COURSES_FILE)
    
    if request.method == 'POST':
        if session.get('role') != 'lecturer':
            return jsonify({'success': False, 'error': 'Only lecturers can create courses'}), 403
        
        data = request.json
        course_id = str(uuid.uuid4())[:8]
        program_type = data.get('program_type', 'regular')
        credit_hours = data.get('credit_hours', 3)
        
        courses[course_id] = {
            'id': course_id,
            'code': data['code'],
            'name': data['name'],
            'credit_hours': credit_hours,
            'program_type': program_type,
            'total_lecture_hours': calendar.get_total_lecture_hours(program_type, credit_hours),
            'lecturer_id': session['user_id'],
            'lecturer_name': session['full_name'],
            'created_at': datetime.now().isoformat()
        }
        save_data(COURSES_FILE, courses)
        return jsonify({'success': True, 'course_id': course_id})
    
    if session.get('role') == 'student':
        enrollments = load_data(ENROLLMENTS_FILE)
        enrolled = enrollments.get(session['user_id'], [])
        return jsonify([c for cid, c in courses.items() if cid in enrolled])
    else:
        return jsonify([c for c in courses.values() if c.get('lecturer_id') == session['user_id']])

@app.route('/api/available_courses')
@login_required
def available_courses():
    if session.get('role') != 'student':
        return jsonify([]), 403
    
    courses = load_data(COURSES_FILE)
    enrollments = load_data(ENROLLMENTS_FILE)
    enrolled = enrollments.get(session['user_id'], [])
    student_program = session.get('program_type', 'regular')
    
    available = [c for cid, c in courses.items() if cid not in enrolled and c.get('program_type', 'regular') == student_program]
    return jsonify(available)

@app.route('/api/enroll', methods=['POST'])
@login_required
def enroll_course():
    if session.get('role') != 'student':
        return jsonify({'success': False, 'error': 'Only students can enroll'}), 403
    
    data = request.json
    course_id = data['course_id']
    enrollments = load_data(ENROLLMENTS_FILE)
    
    if session['user_id'] not in enrollments:
        enrollments[session['user_id']] = []
    
    if course_id in enrollments[session['user_id']]:
        return jsonify({'success': False, 'error': 'Already enrolled'}), 400
    
    enrollments[session['user_id']].append(course_id)
    save_data(ENROLLMENTS_FILE, enrollments)
    return jsonify({'success': True})

@app.route('/api/predict/semester', methods=['POST'])
@login_required
def predict_semester():
    data = request.json
    data['program_type'] = session.get('program_type', 'regular')
    
    weighted_score, metrics = calculate_semester_prediction(data)
    grade, score = get_prediction_grade(weighted_score)
    
    # Save prediction
    predictions = load_data(PREDICTIONS_FILE)
    if session['user_id'] not in predictions:
        predictions[session['user_id']] = []
    
    predictions[session['user_id']].insert(0, {
        'date': datetime.now().isoformat(),
        'type': 'semester',
        'grade': grade,
        'score': score,
        'metrics': metrics,
        'inputs': data,
        'course_id': data.get('course_id')
    })
    
    predictions[session['user_id']] = predictions[session['user_id']][:20]
    save_data(PREDICTIONS_FILE, predictions)
    
    recommendations = generate_recommendations(data, score, metrics)
    
    return jsonify({
        'success': True,
        'grade': grade,
        'score': score,
        'prediction': grade.split(' - ')[0],
        'weighted_score': score,
        'metrics': metrics,
        'recommendations': recommendations
    })

@app.route('/api/predict/weekly', methods=['POST'])
@login_required
def predict_weekly():
    data = request.json
    data['program_type'] = session.get('program_type', 'regular')
    
    weighted_score = calculate_weekly_prediction(data)
    grade, score = get_prediction_grade(weighted_score)
    
    predictions = load_data(PREDICTIONS_FILE)
    if session['user_id'] not in predictions:
        predictions[session['user_id']] = []
    
    predictions[session['user_id']].insert(0, {
        'date': datetime.now().isoformat(),
        'type': 'weekly',
        'grade': grade,
        'score': score,
        'inputs': data,
        'week': data.get('week_number', calendar.get_current_week(data['program_type']))
    })
    
    predictions[session['user_id']] = predictions[session['user_id']][:20]
    save_data(PREDICTIONS_FILE, predictions)
    
    return jsonify({
        'success': True,
        'grade': grade,
        'score': score,
        'prediction': grade.split(' - ')[0],
        'weighted_score': score
    })

@app.route('/api/predict/custom', methods=['POST'])
@login_required
def predict_custom():
    data = request.json
    weighted_score = calculate_custom_prediction(data)
    grade, score = get_prediction_grade(weighted_score)
    
    custom_predictions = load_data(CUSTOM_PREDICTIONS_FILE)
    if session['user_id'] not in custom_predictions:
        custom_predictions[session['user_id']] = []
    
    custom_predictions[session['user_id']].insert(0, {
        'date': datetime.now().isoformat(),
        'grade': grade,
        'score': score,
        'inputs': data,
        'weights': data.get('weights', {})
    })
    
    custom_predictions[session['user_id']] = custom_predictions[session['user_id']][:20]
    save_data(CUSTOM_PREDICTIONS_FILE, custom_predictions)
    
    return jsonify({
        'success': True,
        'grade': grade,
        'score': score,
        'prediction': grade.split(' - ')[0],
        'weighted_score': score
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)