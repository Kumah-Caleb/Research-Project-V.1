from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import hashlib
import secrets
import uuid
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
CORS(app)  # Enable CORS for all origins

# Data file paths
DATA_DIR = 'data'
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
PREDICTIONS_FILE = os.path.join(DATA_DIR, 'predictions.json')
COURSES_FILE = os.path.join(DATA_DIR, 'courses.json')
ENROLLMENTS_FILE = os.path.join(DATA_DIR, 'enrollments.json')

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Initialize data files
def init_data_files():
    """Initialize data files if they don't exist"""
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump({}, f)
    
    if not os.path.exists(PREDICTIONS_FILE):
        with open(PREDICTIONS_FILE, 'w') as f:
            json.dump({}, f)
    
    if not os.path.exists(COURSES_FILE):
        with open(COURSES_FILE, 'w') as f:
            json.dump({}, f)
    
    if not os.path.exists(ENROLLMENTS_FILE):
        with open(ENROLLMENTS_FILE, 'w') as f:
            json.dump({}, f)

def hash_password(password):
    """Hash password for storage"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_data(filepath):
    """Load data from JSON file"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_data(filepath, data):
    """Save data to JSON file"""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

# Initialize data files
init_data_files()

# ============ AAMUSTED Academic Calendar ============
def get_current_week():
    """Calculate current week based on AAMUSTED academic calendar"""
    today = datetime.now()
    # Semester starts August 26
    semester_start = datetime(today.year, 8, 26)
    diff_days = (today - semester_start).days
    week = (diff_days // 7) + 1
    if week < 1:
        week = 1
    if week > 15:
        week = 15
    return week

def calculate_performance_score(data):
    """Calculate performance score based on inputs"""
    attendance = float(data.get('attendance', 0))
    assignments = float(data.get('assignments', 0))
    engagement = float(data.get('engagement', 0))
    study_hours = float(data.get('study_hours', 0))
    previous_grade = float(data.get('previous_grade', 0))
    extra_curricular = float(data.get('extra_curricular', 0))
    parent_education = float(data.get('parent_education', 2))
    
    # Weighted calculation
    weighted_score = (
        attendance * 0.25 +
        assignments * 0.25 +
        engagement * 0.15 +
        (study_hours / 20 * 100) * 0.15 +
        previous_grade * 0.10 +
        (extra_curricular / 5 * 100) * 0.05 +
        (parent_education / 4 * 100) * 0.05
    )
    
    return min(100, max(0, weighted_score))

def get_grade(score):
    """Convert score to AAMUSTED grade"""
    if score >= 85:
        return "A - Excellent"
    elif score >= 80:
        return "B+ - Very Good"
    elif score >= 75:
        return "B - Good"
    elif score >= 70:
        return "C+ - Above Average"
    elif score >= 65:
        return "C - Average"
    elif score >= 60:
        return "D+ - Below Average"
    elif score >= 55:
        return "D - Pass"
    else:
        return "F - Fail"

def generate_recommendations(data, score):
    """Generate personalized recommendations"""
    recommendations = []
    
    attendance = data.get('attendance', 0)
    assignments = data.get('assignments', 0)
    engagement = data.get('engagement', 0)
    study_hours = data.get('study_hours', 0)
    
    if attendance < 70:
        recommendations.append(f"📅 Improve attendance: Currently {attendance}%. Aim for 85%+")
    if assignments < 70:
        recommendations.append(f"📝 Assignment quality: {assignments}%. Review feedback and improve")
    if engagement < 60:
        recommendations.append(f"💬 Class engagement: {engagement}%. Participate more in discussions")
    if study_hours < 10:
        recommendations.append(f"⏰ Study hours: {study_hours}/week. Aim for 10-15 hours")
    
    if score >= 85:
        recommendations.append("🌟 Excellent performance! Keep up the great work!")
    elif score >= 70:
        recommendations.append("👍 Good progress! Focus on weaker areas to reach excellence")
    elif score >= 55:
        recommendations.append("⚠️ You're at risk. Seek academic support immediately")
    else:
        recommendations.append("🆘 Critical: Contact academic advisor for intervention")
    
    return recommendations

# ============ API ENDPOINTS ============

@app.route('/')
def home():
    """API home endpoint"""
    return jsonify({
        'name': 'AAMUSTED Student Performance Predictor API',
        'status': 'running',
        'version': '2.0',
        'frontend': 'https://kumah-caleb.github.io/Research-Project-V.1/',
        'endpoints': {
            'health': 'GET /health',
            'predict': 'POST /predict',
            'register': 'POST /api/register',
            'login': 'POST /api/login',
            'logout': 'POST /api/logout',
            'courses': 'GET /api/courses',
            'students': 'GET /api/students',
            'profile': 'GET/PUT /api/profile'
        }
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'message': 'Server is running',
        'current_week': get_current_week()
    })

@app.route('/api/register', methods=['POST'])
def api_register():
    """User registration endpoint"""
    try:
        data = request.json
        users = load_data(USERS_FILE)
        
        # Check if username exists
        for user_id, user in users.items():
            if user.get('username') == data['username']:
                return jsonify({'success': False, 'error': 'Username already exists'}), 400
            if user.get('email') == data['email']:
                return jsonify({'success': False, 'error': 'Email already registered'}), 400
        
        # Create new user
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
        
        return jsonify({
            'success': True,
            'user': {
                'id': user_id,
                'username': data['username'],
                'full_name': data['full_name'],
                'role': data.get('role', 'student'),
                'program_type': data.get('program_type', 'regular')
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def api_login():
    """User login endpoint"""
    try:
        data = request.json
        users = load_data(USERS_FILE)
        
        for user_id, user in users.items():
            if user['username'] == data['username'] and user['password'] == hash_password(data['password']):
                return jsonify({
                    'success': True,
                    'user': {
                        'id': user_id,
                        'username': user['username'],
                        'full_name': user['full_name'],
                        'role': user['role'],
                        'program_type': user.get('program_type', 'regular'),
                        'index_number': user.get('index_number', ''),
                        'email': user.get('email', ''),
                        'department': user.get('department', ''),
                        'level': user.get('level', '')
                    }
                })
        
        return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def api_logout():
    """Logout endpoint (no session needed for static frontend)"""
    return jsonify({'success': True})

@app.route('/api/predict', methods=['POST'])
def api_predict():
    """Make a prediction"""
    try:
        data = request.json
        
        # Calculate score
        weighted_score = calculate_performance_score(data)
        grade = get_grade(weighted_score)
        confidence = min(95, max(60, weighted_score))
        
        # Save prediction (if user_id provided)
        user_id = data.get('user_id')
        if user_id:
            predictions = load_data(PREDICTIONS_FILE)
            if user_id not in predictions:
                predictions[user_id] = []
            
            predictions[user_id].insert(0, {
                'date': datetime.now().isoformat(),
                'grade': grade,
                'score': weighted_score,
                'confidence': confidence,
                'inputs': data
            })
            
            # Keep only last 20 predictions
            predictions[user_id] = predictions[user_id][:20]
            save_data(PREDICTIONS_FILE, predictions)
        
        # Generate recommendations
        recommendations = generate_recommendations(data, weighted_score)
        
        return jsonify({
            'success': True,
            'prediction': grade.split(' - ')[0],
            'grade': grade,
            'score': weighted_score,
            'weighted_score': weighted_score,
            'confidence': confidence,
            'recommendations': recommendations
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/predict/weekly', methods=['POST'])
def api_predict_weekly():
    """Weekly prediction endpoint"""
    try:
        data = request.json
        
        weekly_attendance = float(data.get('weekly_attendance', 0))
        weekly_assignments = float(data.get('weekly_assignments', 0))
        weekly_engagement = float(data.get('weekly_engagement', 0))
        weekly_study_hours = float(data.get('weekly_study_hours', 0))
        midterm_grade = float(data.get('midterm_grade', 0))
        weeks_completed = float(data.get('weeks_completed', 1))
        
        # Calculate weekly score
        weekly_score = (
            weekly_attendance * 0.25 +
            weekly_assignments * 0.25 +
            weekly_engagement * 0.20 +
            (weekly_study_hours / 20 * 100) * 0.20 +
            midterm_grade * 0.10
        )
        
        # Project final score
        weeks_remaining = 15 - weeks_completed
        projected_score = (weekly_score * weeks_completed + 70 * weeks_remaining) / 15
        
        grade = get_grade(projected_score)
        
        # Generate weekly recommendations
        recommendations = []
        if weekly_attendance < 70:
            recommendations.append(f"📅 Attendance: {weekly_attendance}%. Aim for 85%+")
        if weekly_assignments < 70:
            recommendations.append(f"📝 Assignments: {weekly_assignments}%. Improve quality")
        if weekly_engagement < 60:
            recommendations.append(f"💬 Engagement: {weekly_engagement}%. Participate more")
        if weekly_study_hours < 10:
            recommendations.append(f"⏰ Study hours: {weekly_study_hours}/week. Aim for 10-15 hours")
        
        return jsonify({
            'success': True,
            'grade': grade,
            'score': projected_score,
            'weekly_score': weekly_score,
            'recommendations': recommendations
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/courses', methods=['GET', 'POST'])
def api_courses():
    """Get or create courses"""
    courses = load_data(COURSES_FILE)
    
    if request.method == 'POST':
        data = request.json
        course_id = str(uuid.uuid4())[:8]
        courses[course_id] = {
            'id': course_id,
            'code': data['code'],
            'name': data['name'],
            'credit_hours': data.get('credit_hours', 3),
            'program_type': data.get('program_type', 'regular'),
            'lecturer_id': data.get('lecturer_id'),
            'lecturer_name': data.get('lecturer_name'),
            'created_at': datetime.now().isoformat()
        }
        save_data(COURSES_FILE, courses)
        return jsonify({'success': True, 'course': courses[course_id]})
    
    return jsonify(list(courses.values()))

@app.route('/api/enroll', methods=['POST'])
def api_enroll():
    """Enroll student in course"""
    try:
        data = request.json
        student_id = data.get('student_id')
        course_id = data.get('course_id')
        
        enrollments = load_data(ENROLLMENTS_FILE)
        
        if student_id not in enrollments:
            enrollments[student_id] = []
        
        if course_id in enrollments[student_id]:
            return jsonify({'success': False, 'error': 'Already enrolled'}), 400
        
        enrollments[student_id].append(course_id)
        save_data(ENROLLMENTS_FILE, enrollments)
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/students', methods=['GET'])
def api_students():
    """Get all students (for lecturer view)"""
    users = load_data(USERS_FILE)
    students = [user for user in users.values() if user.get('role') == 'student']
    return jsonify(students)

@app.route('/api/history', methods=['GET'])
def api_history():
    """Get prediction history for a user"""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify([])
    
    predictions = load_data(PREDICTIONS_FILE)
    return jsonify(predictions.get(user_id, []))

@app.route('/api/profile', methods=['GET', 'PUT'])
def api_profile():
    """Get or update user profile"""
    try:
        data = request.json
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'success': False, 'error': 'User ID required'}), 400
        
        users = load_data(USERS_FILE)
        
        if user_id not in users:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        if request.method == 'PUT':
            # Update profile
            if 'full_name' in data:
                users[user_id]['full_name'] = data['full_name']
            if 'email' in data:
                users[user_id]['email'] = data['email']
            if 'index_number' in data:
                users[user_id]['index_number'] = data['index_number']
            if 'department' in data:
                users[user_id]['department'] = data['department']
            if 'level' in data:
                users[user_id]['level'] = data['level']
            if 'program_type' in data:
                users[user_id]['program_type'] = data['program_type']
            
            save_data(USERS_FILE, users)
            
            return jsonify({
                'success': True,
                'user': users[user_id]
            })
        else:
            # GET profile
            return jsonify({
                'success': True,
                'user': users[user_id]
            })
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============ RUN APP ============
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print("=" * 50)
    print("AAMUSTED Student Performance Predictor API")
    print("=" * 50)
    print(f"🚀 Server starting on port {port}")
    print(f"📡 Health check: http://localhost:{port}/health")
    print(f"🔮 Prediction endpoint: http://localhost:{port}/api/predict")
    print("=" * 50)
    app.run(host='0.0.0.0', port=port, debug=False)