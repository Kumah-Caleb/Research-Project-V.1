# app.py - Complete Flask Application with All Features
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import joblib
import pandas as pd
import numpy as np
import os
import json
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from models import db, User, Prediction, Course, UserCourse

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'aamusted-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///aamusted.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
CORS(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_page'

# ML Model variables
model = None
scaler = None
label_encoder = None
feature_columns = None

def load_ml_model():
    global model, scaler, label_encoder, feature_columns
    try:
        model = joblib.load('model.pkl')
        scaler = joblib.load('scaler.pkl')
        label_encoder = joblib.load('label_encoder.pkl')
        feature_columns = joblib.load('feature_columns.pkl')
        print("✅ ML Model loaded successfully")
        return True
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return False

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def predict_performance(attendance, assignments, engagement, study_hours, previous_grade, extra_curricular, parent_education):
    try:
        input_dict = {
            'attendance': attendance,
            'assignments': assignments,
            'engagement': engagement,
            'study_hours': study_hours,
            'previous_grade': previous_grade,
            'extra_curricular': extra_curricular,
            'parent_education': parent_education
        }
        
        input_data = pd.DataFrame([[input_dict[col] for col in feature_columns]], columns=feature_columns)
        input_scaled = scaler.transform(input_data)
        prediction_encoded = model.predict(input_scaled)[0]
        prediction_class = label_encoder.inverse_transform([prediction_encoded])[0]
        probabilities = model.predict_proba(input_scaled)[0]
        confidence = float(np.max(probabilities) * 100)
        
        study_hours_percent = (study_hours / 20) * 100
        extra_curricular_percent = (extra_curricular / 5) * 100
        parent_education_percent = (parent_education / 4) * 100
        
        weighted_score = (
            attendance * 0.20 +
            assignments * 0.20 +
            engagement * 0.15 +
            study_hours_percent * 0.15 +
            previous_grade * 0.15 +
            extra_curricular_percent * 0.10 +
            parent_education_percent * 0.05
        )
        
        return prediction_class, confidence, weighted_score
    except Exception as e:
        print(f"Prediction error: {e}")
        return "Error", 0, 0

# ============ PAGE ROUTES ============

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/student_dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        return redirect(url_for('lecturer_dashboard'))
    return render_template('student_dashboard.html', user=current_user)

@app.route('/lecturer_dashboard')
@login_required
def lecturer_dashboard():
    if current_user.role != 'lecturer':
        return redirect(url_for('student_dashboard'))
    return render_template('lecturer_dashboard.html', user=current_user)

@app.route('/history')
@login_required
def history():
    return render_template('history.html', user=current_user)

# ============ AUTH API ============

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    
    if user and check_password_hash(user.password_hash, data['password']):
        login_user(user)
        return jsonify({'success': True, 'role': user.role, 'redirect': f'/{user.role}_dashboard'})
    return jsonify({'success': False, 'error': 'Invalid credentials'})

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.json
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'success': False, 'error': 'Username already exists'})
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'success': False, 'error': 'Email already registered'})
    
    user = User(
        username=data['username'],
        email=data['email'],
        password_hash=generate_password_hash(data['password']),
        role=data.get('role', 'student'),
        full_name=data['full_name'],
        index_number=data.get('index_number')
    )
    db.session.add(user)
    db.session.commit()
    
    login_user(user)
    return jsonify({'success': True, 'role': user.role})

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# ============ COURSE MANAGEMENT API ============

@app.route('/api/my_courses', methods=['GET'])
@login_required
def my_courses():
    """Get courses for current user"""
    if current_user.role == 'lecturer':
        courses = Course.query.filter_by(lecturer_id=current_user.id).all()
        return jsonify([{
            'id': c.id,
            'name': c.name,
            'code': c.code,
            'credit_hours': c.credit_hours,
            'student_count': UserCourse.query.filter_by(course_id=c.id).count()
        } for c in courses])
    else:
        # Student
        user_courses = UserCourse.query.filter_by(user_id=current_user.id).all()
        courses_data = []
        for uc in user_courses:
            c = uc.course
            courses_data.append({
                'id': c.id,
                'name': c.name,
                'code': c.code,
                'credit_hours': c.credit_hours,
                'attendance': uc.attendance,
                'assignments': uc.assignments,
                'engagement': uc.engagement,
                'study_hours': uc.study_hours,
                'previous_grade': uc.previous_grade,
                'predicted_grade': uc.predicted_grade,
                'weighted_score': uc.weighted_score
            })
        return jsonify(courses_data)

@app.route('/api/my_courses', methods=['POST', 'DELETE'])
@login_required
def manage_courses():
    if request.method == 'POST':
        data = request.json
        course = Course(
            name=data['name'],
            code=data['code'],
            credit_hours=data.get('credit_hours', 3),
            lecturer_id=current_user.id if current_user.role == 'lecturer' else None
        )
        db.session.add(course)
        db.session.commit()
        
        if current_user.role == 'student':
            enrollment = UserCourse(user_id=current_user.id, course_id=course.id)
            db.session.add(enrollment)
            db.session.commit()
        
        return jsonify({'success': True, 'course_id': course.id})
    
    elif request.method == 'DELETE':
        data = request.json
        course_id = data.get('course_id')
        
        if current_user.role == 'lecturer':
            course = Course.query.get_or_404(course_id)
            if course.lecturer_id != current_user.id:
                return jsonify({'error': 'Not your course'}), 403
            UserCourse.query.filter_by(course_id=course_id).delete()
            db.session.delete(course)
        else:
            enrollment = UserCourse.query.filter_by(user_id=current_user.id, course_id=course_id).first()
            if enrollment:
                db.session.delete(enrollment)
        
        db.session.commit()
        return jsonify({'success': True})

@app.route('/api/available_courses')
@login_required
def available_courses():
    """Get all courses that the student is not already enrolled in"""
    if current_user.role != 'student':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get courses the student is already enrolled in
    enrolled_ids = [uc.course_id for uc in current_user.courses]
    
    # Get all courses created by lecturers (not enrolled by student)
    if enrolled_ids:
        available = Course.query.filter(
            Course.lecturer_id.isnot(None),
            Course.id.notin_(enrolled_ids)
        ).all()
    else:
        available = Course.query.filter(Course.lecturer_id.isnot(None)).all()
    
    courses_list = []
    for c in available:
        lecturer_name = c.lecturer.full_name if c.lecturer else 'Unknown'
        courses_list.append({
            'id': c.id,
            'name': c.name,
            'code': c.code,
            'credit_hours': c.credit_hours,
            'lecturer_name': lecturer_name
        })
    
    return jsonify(courses_list)

@app.route('/api/enroll', methods=['POST'])
@login_required
def enroll_in_course():
    """Enroll student in a course"""
    if current_user.role != 'student':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    course_id = data.get('course_id')
    
    # Check if course exists
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'error': 'Course not found'}), 404
    
    # Check if already enrolled
    existing = UserCourse.query.filter_by(
        user_id=current_user.id, 
        course_id=course_id
    ).first()
    
    if existing:
        return jsonify({'error': 'Already enrolled in this course'}), 400
    
    # Create enrollment
    enrollment = UserCourse(
        user_id=current_user.id, 
        course_id=course_id,
        attendance=0,
        assignments=0,
        engagement=0,
        study_hours=10,
        previous_grade=65
    )
    db.session.add(enrollment)
    db.session.commit()
    
    return jsonify({'success': True, 'course_name': course.name})

@app.route('/api/lecturer/courses/<int:course_id>/students')
@login_required
def course_students(course_id):
    if current_user.role != 'lecturer':
        return jsonify({'error': 'Unauthorized'}), 403
    
    course = Course.query.get_or_404(course_id)
    if course.lecturer_id != current_user.id:
        return jsonify({'error': 'Not your course'}), 403
    
    enrollments = UserCourse.query.filter_by(course_id=course_id).all()
    students_data = []
    for enrollment in enrollments:
        student = User.query.get(enrollment.user_id)
        students_data.append({
            'id': student.id,
            'name': student.full_name,
            'index': student.index_number,
            'predicted_grade': enrollment.predicted_grade,
            'weighted_score': enrollment.weighted_score,
            'attendance': enrollment.attendance,
            'assignments': enrollment.assignments,
            'engagement': enrollment.engagement
        })
    
    return jsonify({'course': {'id': course.id, 'name': course.name, 'code': course.code}, 'students': students_data})

@app.route('/api/student/<int:student_id>')
@login_required
def get_student_data(student_id):
    if current_user.role != 'lecturer' and current_user.id != student_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    student = User.query.get_or_404(student_id)
    courses = UserCourse.query.filter_by(user_id=student.id).all()
    
    return jsonify({
        'student': {
            'name': student.full_name,
            'index': student.index_number,
            'email': student.email,
            'joined': student.created_at.strftime('%Y-%m-%d')
        },
        'courses': [{
            'id': uc.course.id,
            'name': uc.course.name,
            'code': uc.course.code,
            'predicted_grade': uc.predicted_grade,
            'weighted_score': uc.weighted_score,
            'attendance': uc.attendance,
            'assignments': uc.assignments,
            'engagement': uc.engagement
        } for uc in courses]
    })

# ============ PREDICTION API ============

@app.route('/api/predict', methods=['POST'])
@login_required
def api_predict():
    data = request.json
    course_id = data.get('course_id')
    student_id = data.get('student_id')
    
    attendance = float(data['attendance'])
    assignments = float(data['assignments'])
    engagement = float(data['engagement'])
    study_hours = float(data.get('study_hours', 10))
    previous_grade = float(data.get('previous_grade', 65))
    extra_curricular = float(data.get('extra_curricular', 2))
    parent_education = float(data.get('parent_education', 2))
    
    prediction, confidence, weighted_score = predict_performance(
        attendance, assignments, engagement, study_hours, previous_grade,
        extra_curricular, parent_education
    )
    
    # Determine which user to save prediction for
    target_user_id = student_id if student_id else current_user.id
    
    # If student is updating their own course data
    if current_user.role == 'student' and course_id:
        user_course = UserCourse.query.filter_by(user_id=current_user.id, course_id=course_id).first()
        if user_course:
            user_course.attendance = attendance
            user_course.assignments = assignments
            user_course.engagement = engagement
            user_course.study_hours = study_hours
            user_course.previous_grade = previous_grade
            user_course.predicted_grade = prediction
            user_course.weighted_score = weighted_score
            db.session.commit()
    
    # Save prediction to history
    pred_record = Prediction(
        user_id=target_user_id,
        course_id=course_id,
        attendance=attendance,
        assignments=assignments,
        engagement=engagement,
        study_hours=study_hours,
        previous_grade=previous_grade,
        extra_curricular=extra_curricular,
        parent_education=parent_education,
        predicted_grade=prediction,
        weighted_score=weighted_score,
        confidence=confidence
    )
    db.session.add(pred_record)
    db.session.commit()
    
    return jsonify({'success': True, 'prediction': prediction, 'confidence': confidence, 'weighted_score': weighted_score})

@app.route('/api/course/<int:course_id>/strengths')
@login_required
def analyze_course_strengths(course_id):
    if current_user.role != 'student':
        return jsonify({'error': 'Unauthorized'}), 403
    
    user_course = UserCourse.query.filter_by(user_id=current_user.id, course_id=course_id).first()
    if not user_course:
        return jsonify({'error': 'Not enrolled'}), 404
    
    strengths = []
    weaknesses = []
    recommendations = []
    
    metrics = [
        ('attendance', user_course.attendance, 'attendance', '📅'),
        ('assignments', user_course.assignments, 'assignment completion', '📝'),
        ('engagement', user_course.engagement, 'class engagement', '💬'),
        ('study_hours', (user_course.study_hours / 20) * 100, 'study habits', '📚')
    ]
    
    for name, value, display, icon in metrics:
        if value >= 70:
            strengths.append(f"{icon} {display.capitalize()}: {value:.0f}% - Excellent!")
        elif value < 50 and value > 0:
            weaknesses.append(f"{icon} {display.capitalize()}: {value:.0f}% - Needs improvement")
            recommendations.append(f"Focus on improving {display}")
    
    if user_course.weighted_score:
        if user_course.weighted_score >= 80:
            strengths.append(f"🎯 Overall performance: {user_course.weighted_score:.0f}% - Outstanding!")
        elif user_course.weighted_score < 60:
            weaknesses.append(f"⚠️ Overall performance: {user_course.weighted_score:.0f}% - At risk")
            recommendations.append("Seek academic support and review study strategies")
    
    return jsonify({'strengths': strengths, 'weaknesses': weaknesses, 'recommendations': recommendations})

@app.route('/api/history')
@login_required
def get_history():
    predictions = Prediction.query.filter_by(user_id=current_user.id).order_by(Prediction.created_at.desc()).limit(50).all()
    return jsonify([{
        'id': p.id,
        'predicted_grade': p.predicted_grade,
        'weighted_score': p.weighted_score,
        'confidence': p.confidence,
        'created_at': p.created_at.strftime('%Y-%m-%d %H:%M'),
        'course_id': p.course_id
    } for p in predictions])

@app.route('/api/study_schedule')
@login_required
def get_study_schedule():
    if current_user.role != 'student':
        return jsonify([])
    
    user_courses = UserCourse.query.filter_by(user_id=current_user.id).all()
    schedule = []
    
    for uc in user_courses:
        if uc.weighted_score:
            if uc.weighted_score < 50:
                hours = 8
                tip = "🔴 Critical: Focus on fundamentals. Attend extra classes."
                priority = "High"
            elif uc.weighted_score < 70:
                hours = 5
                tip = "🟡 Good progress: Practice more. Review weak areas."
                priority = "Medium"
            else:
                hours = 3
                tip = "🟢 Excellent: Maintain momentum. Help peers to reinforce learning."
                priority = "Low"
            
            schedule.append({
                'course': uc.course.name,
                'code': uc.course.code,
                'recommended_hours': hours,
                'tip': tip,
                'priority': priority,
                'current_score': round(uc.weighted_score, 1)
            })
    
    priority_order = {'High': 0, 'Medium': 1, 'Low': 2}
    schedule.sort(key=lambda x: priority_order[x['priority']])
    return jsonify(schedule)

@app.route('/api/download_report')
@login_required
def download_report():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    title = Paragraph(f"Student Performance Report - {current_user.full_name}", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    info = [
        ["Name:", current_user.full_name],
        ["Index Number:", current_user.index_number or "N/A"],
        ["Email:", current_user.email],
        ["Report Date:", datetime.now().strftime('%Y-%m-%d %H:%M')]
    ]
    info_table = Table(info, colWidths=[100, 300])
    info_table.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
    story.append(info_table)
    story.append(Spacer(1, 20))
    
    if current_user.role == 'student':
        user_courses = UserCourse.query.filter_by(user_id=current_user.id).all()
        course_data = [["Course", "Code", "Predicted Grade", "Score"]]
        for uc in user_courses:
            course_data.append([uc.course.name, uc.course.code, uc.predicted_grade or "Pending", f"{uc.weighted_score:.1f}%" if uc.weighted_score else "N/A"])
        course_table = Table(course_data, colWidths=[200, 80, 100, 80])
        course_table.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
        story.append(course_table)
    
    doc.build(buffer)
    buffer.seek(0)
    return send_file(buffer, download_name=f"{current_user.index_number or current_user.username}_report.pdf", as_attachment=True, mimetype='application/pdf')

@app.route('/api/students')
@login_required
def get_students():
    if current_user.role != 'lecturer':
        return jsonify({'error': 'Unauthorized'}), 403
    students = User.query.filter_by(role='student').all()
    return jsonify([{'id': s.id, 'name': s.full_name, 'index': s.index_number, 'email': s.email} for s in students])

# ============ RUN APP ============

# At the very bottom of app.py, replace the if __name__ == '__main__' section with:
if __name__ == '__main__':
    # This is only for local development
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=False, host='0.0.0.0', port=port)
else:
    # This is for production (gunicorn)
    # Make sure the ML model is loaded
    with app.app_context():
        load_ml_model()