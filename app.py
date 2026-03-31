"""
USTED Three-Format Academic Predictor - Backend API
Endpoints: /api/predict-semester, /api/predict-weekly, /api/predict-module
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
import secrets
import hashlib
import re
from datetime import datetime

# ============================================
# DATA STORAGE
# ============================================

users_db = {}
tokens_db = {}
predictions_db = {}
courses_db = {}
enrollments_db = {}
user_counter = 1
prediction_counter = 1
course_counter = 1
enrollment_counter = 1

# Sample courses for testing
courses_db[1] = {
    "id": 1,
    "course_code": "ITE301",
    "course_name": "Advanced Web Development",
    "credits": 3,
    "lecturer_id": 1001,
    "lecturer_name": "Dr. John Smith",
    "department": "Information Technology",
    "semester": "2024/2025",
    "capacity": 30,
    "enrolled": 0,
    "created_at": datetime.utcnow().isoformat()
}

courses_db[2] = {
    "id": 2,
    "course_code": "ITE302",
    "course_name": "Database Management Systems",
    "credits": 3,
    "lecturer_id": 1001,
    "lecturer_name": "Dr. John Smith",
    "department": "Information Technology",
    "semester": "2024/2025",
    "capacity": 25,
    "enrolled": 0,
    "created_at": datetime.utcnow().isoformat()
}

course_counter = 3

# Ensure users have proper role
for user in users_db.values():
    if "role" not in user:
        user["role"] = "student"

# ============================================
# HELPER FUNCTIONS
# ============================================

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain, hashed):
    return hash_password(plain) == hashed

def generate_token():
    return secrets.token_urlsafe(32)

def grade_to_numeric(grade):
    grade_map = {
        'A': 4.0, 'A-': 3.7, 'B+': 3.3, 'B': 3.0,
        'B-': 2.7, 'C+': 2.3, 'C': 2.0, 'C-': 1.7,
        'D+': 1.3, 'D': 1.0, 'F': 0.0
    }
    return grade_map.get(grade, 2.0)

def numeric_to_grade(value):
    if value >= 3.7: return 'A'
    if value >= 3.3: return 'B+'
    if value >= 3.0: return 'B'
    if value >= 2.7: return 'B-'
    if value >= 2.3: return 'C+'
    if value >= 2.0: return 'C'
    if value >= 1.7: return 'C-'
    if value >= 1.3: return 'D+'
    if value >= 1.0: return 'D'
    return 'F'

def get_grade_description(grade):
    descriptions = {
        'A': 'Excellent - Outstanding performance',
        'A-': 'Excellent - Very strong performance',
        'B+': 'Very Good - Above average performance',
        'B': 'Good - Solid performance',
        'B-': 'Good - Satisfactory performance',
        'C+': 'Average - Acceptable performance',
        'C': 'Average - Fair performance',
        'C-': 'Average - Below satisfactory',
        'D+': 'Poor - Needs improvement',
        'D': 'Poor - Significant improvement needed',
        'F': 'Failing - Immediate intervention required'
    }
    return descriptions.get(grade, 'Grade not recognized')

def get_grade_category(grade):
    categories = {
        'A': 'Excellent', 'A-': 'Excellent',
        'B+': 'Very Good', 'B': 'Good', 'B-': 'Good',
        'C+': 'Average', 'C': 'Average', 'C-': 'Average',
        'D+': 'Poor', 'D': 'Poor',
        'F': 'Failing'
    }
    return categories.get(grade, 'Unknown')

def get_parental_factor(parental_level):
    factors = {
        "none": 0.6,
        "primary": 0.7,
        "secondary": 0.8,
        "tertiary": 0.9,
        "postgraduate": 1.0
    }
    return factors.get(parental_level.lower(), 0.8)

def get_semester_type_factor(semester_type):
    factors = {
        "regular": 1.0,
        "non-regular": 0.92,
        "modular": 0.88,
        "sandwich": 0.95,
        "distance": 0.85
    }
    return factors.get(semester_type.lower(), 1.0)

def get_module_type_factor(module_type):
    factors = {
        "core": 0.95,
        "elective": 1.05,
        "project": 0.90,
        "lab": 0.92
    }
    return factors.get(module_type.lower(), 1.0)

def calculate_base_score(assignments, attendance, engagement, parental_level, study_hours):
    assignments_factor = assignments / 100
    attendance_factor = attendance / 100
    engagement_factor = engagement / 100
    parental_factor = get_parental_factor(parental_level)
    study_factor = min(1.0, study_hours / 25)

    score = (
        assignments_factor * 0.30 +
        attendance_factor * 0.25 +
        engagement_factor * 0.25 +
        parental_factor * 0.10 +
        study_factor * 0.10
    )
    return score * 4.0

def calculate_confidence(scores):
    base_confidence = 50
    for s in scores:
        base_confidence += (s / 4.0) * 10
    return min(95, max(50, base_confidence))

def generate_recommendations(grade, scores, factors):
    recommendations = []

    if grade in ['D', 'F']:
        recommendations.append("🚨 URGENT: Schedule meeting with academic advisor immediately")

    if factors.get("assignments", 70) < 70:
        recommendations.append("📝 IMPROVE ASSIGNMENTS: Complete all assignments on time.")

    if factors.get("attendance", 75) < 80:
        recommendations.append("📅 BOOST ATTENDANCE: Regular attendance is crucial.")

    if factors.get("engagement", 65) < 70:
        recommendations.append("💬 INCREASE ENGAGEMENT: Participate in class discussions.")

    if factors.get("study_hours", 10) < 15:
        recommendations.append(f"⏰ STUDY MORE: Current {factors.get('study_hours', 10)} hrs/week. Aim for 15-20 hrs.")

    if factors.get("parental_level", "secondary") in ["none", "primary"]:
        recommendations.append("👨‍👩‍👧 SEEK SUPPORT: Discuss your academic goals with family.")

    if not recommendations:
        recommendations.append("🌟 EXCELLENT! You're on track. Maintain consistency.")

    return " | ".join(recommendations)

# ============================================
# PYDANTIC MODELS
# ============================================

class SemesterPredictionRequest(BaseModel):
    semester_type: str = "regular"
    current_semester: int = 3
    total_semesters: int = 8
    assignments: int = Field(75, ge=0, le=100)
    attendance: int = Field(80, ge=0, le=100)
    engagement: int = Field(70, ge=0, le=100)
    parental_level: str = "secondary"
    study_hours: int = Field(12, ge=0, le=40)
    previous_gpa: float = Field(3.0, ge=0, le=4.0)

class WeeklyPredictionRequest(BaseModel):
    week_number: int = Field(8, ge=1, le=16)
    total_weeks: int = Field(16, ge=12, le=20)
    assignments: int = Field(70, ge=0, le=100)
    attendance: int = Field(75, ge=0, le=100)
    engagement: int = Field(65, ge=0, le=100)
    parental_level: str = "secondary"
    study_hours: int = Field(10, ge=0, le=40)
    consistency: int = Field(70, ge=0, le=100)
    previous_gpa: float = Field(3.0, ge=0, le=4.0)
    semester_type: str = "regular"

class ModulePredictionRequest(BaseModel):
    module_code: str = "ITE301"
    module_type: str = "core"
    credit_hours: int = Field(3, ge=1, le=6)
    assignments: int = Field(80, ge=0, le=100)
    attendance: int = Field(85, ge=0, le=100)
    engagement: int = Field(75, ge=0, le=100)
    parental_level: str = "secondary"
    study_hours: int = Field(8, ge=0, le=40)
    previous_gpa: float = Field(3.0, ge=0, le=4.0)
    semester_type: str = "regular"

class PredictionResponse(BaseModel):
    predicted_grade: str
    grade_description: str
    grade_category: str
    confidence: float
    recommendations: str
    factors_summary: str

# ============================================
# FASTAPI APP
# ============================================

app = FastAPI(title="USTED Three-Format Predictor", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# AUTH ENDPOINTS
# ============================================

@app.get("/")
def root():
    return {"message": "USTED Three-Format Predictor API", "version": "3.0"}

@app.post("/api/register")
def register(user: dict):
    global user_counter
    user_id = user_counter
    user_counter += 1
    users_db[user_id] = {
        "id": user_id,
        "username": user.get("username"),
        "password_hash": hash_password(user.get("password", "")),
        "email": user.get("email"),
        "full_name": user.get("full_name"),
        "student_id": user.get("student_id"),
        "role": "student",
        "created_at": datetime.utcnow().isoformat()
    }
    return {"id": user_id, "username": user.get("username")}

@app.post("/api/login")
def login(request: dict):
    """Login for both students and lecturers"""
    username = request.get("username")
    password = request.get("password")
    
    for u in users_db.values():
        if (u["username"] == username or u.get("email") == username) and verify_password(password, u["password_hash"]):
            token = generate_token()
            tokens_db[token] = u["id"]
            return {
                "token": token,
                "user": {
                    "id": u["id"],
                    "username": u["username"],
                    "full_name": u["full_name"],
                    "email": u["email"],
                    "role": u.get("role", "student"),
                    "student_id": u.get("student_id", ""),
                    "lecturer_id": u.get("lecturer_id", "")
                }
            }
    raise HTTPException(401, "Invalid credentials")

@app.get("/api/verify")
def verify(token: str):
    if token in tokens_db:
        user_id = tokens_db[token]
        u = users_db[user_id]
        return {
            "id": u["id"],
            "username": u["username"],
            "full_name": u["full_name"],
            "email": u["email"],
            "student_id": u["student_id"]
        }
    raise HTTPException(401, "Invalid token")

# ============================================
# PREDICTION ENDPOINTS
# ============================================

@app.post("/api/predict-semester", response_model=PredictionResponse)
def predict_semester(request: SemesterPredictionRequest, token: str):
    global prediction_counter

    if token not in tokens_db:
        raise HTTPException(401, "Invalid token")

    user_id = tokens_db[token]

    base_score = calculate_base_score(
        request.assignments,
        request.attendance,
        request.engagement,
        request.parental_level,
        request.study_hours
    )

    semester_factor = get_semester_type_factor(request.semester_type)
    progression_factor = 1 - ((request.current_semester - 1) / request.total_semesters) * 0.15

    final_score = base_score * semester_factor * progression_factor
    final_score = (final_score * 0.8) + (request.previous_gpa * 0.2)
    final_score = min(4.0, max(0, final_score))

    predicted_grade = numeric_to_grade(final_score)
    scores = [base_score, semester_factor * 4, progression_factor * 4]
    confidence = calculate_confidence(scores)

    factors_summary = f"Semester: {request.semester_type} | Assignments: {request.assignments}% | Attendance: {request.attendance}% | Engagement: {request.engagement}% | Study Hours: {request.study_hours}/week"

    recommendations = generate_recommendations(predicted_grade, [final_score], {
        "assignments": request.assignments,
        "attendance": request.attendance,
        "engagement": request.engagement,
        "study_hours": request.study_hours,
        "parental_level": request.parental_level
    })

    prediction_id = prediction_counter
    prediction_counter += 1

    predictions_db[prediction_id] = {
        "id": prediction_id,
        "user_id": user_id,
        "format": "semester",
        "predicted_grade": predicted_grade,
        "confidence": confidence,
        "input_data": request.dict(),
        "created_at": datetime.utcnow().isoformat()
    }

    return PredictionResponse(
        predicted_grade=predicted_grade,
        grade_description=get_grade_description(predicted_grade),
        grade_category=get_grade_category(predicted_grade),
        confidence=round(confidence, 1),
        recommendations=recommendations,
        factors_summary=factors_summary
    )

@app.post("/api/predict-weekly", response_model=PredictionResponse)
def predict_weekly(request: WeeklyPredictionRequest, token: str):
    global prediction_counter

    if token not in tokens_db:
        raise HTTPException(401, "Invalid token")

    user_id = tokens_db[token]

    base_score = calculate_base_score(
        request.assignments,
        request.attendance,
        request.engagement,
        request.parental_level,
        request.study_hours
    )

    week_factor = 1 - ((request.week_number - 1) / request.total_weeks) * 0.1
    consistency_factor = 0.9 + (request.consistency / 100) * 0.1
    semester_factor = get_semester_type_factor(request.semester_type)

    final_score = base_score * week_factor * consistency_factor * semester_factor
    final_score = (final_score * 0.8) + (request.previous_gpa * 0.2)
    final_score = min(4.0, max(0, final_score))

    predicted_grade = numeric_to_grade(final_score)
    scores = [base_score, week_factor * 4, consistency_factor * 4]
    confidence = calculate_confidence(scores)

    factors_summary = f"Week {request.week_number}/{request.total_weeks} | Consistency: {request.consistency}% | Assignments: {request.assignments}% | Attendance: {request.attendance}% | Study Hours: {request.study_hours}/week"

    recommendations = generate_recommendations(predicted_grade, [final_score], {
        "assignments": request.assignments,
        "attendance": request.attendance,
        "engagement": request.engagement,
        "study_hours": request.study_hours,
        "parental_level": request.parental_level
    })

    if request.consistency < 70:
        recommendations = f"📊 IMPROVE CONSISTENCY: Your consistency score is {request.consistency}%. | {recommendations}"

    prediction_id = prediction_counter
    prediction_counter += 1

    predictions_db[prediction_id] = {
        "id": prediction_id,
        "user_id": user_id,
        "format": "weekly",
        "predicted_grade": predicted_grade,
        "confidence": confidence,
        "input_data": request.dict(),
        "created_at": datetime.utcnow().isoformat()
    }

    return PredictionResponse(
        predicted_grade=predicted_grade,
        grade_description=get_grade_description(predicted_grade),
        grade_category=get_grade_category(predicted_grade),
        confidence=round(confidence, 1),
        recommendations=recommendations,
        factors_summary=factors_summary
    )

@app.post("/api/predict-module", response_model=PredictionResponse)
def predict_module(request: ModulePredictionRequest, token: str):
    global prediction_counter

    if token not in tokens_db:
        raise HTTPException(401, "Invalid token")

    user_id = tokens_db[token]

    if request.module_code and not re.match(r'^[A-Z]{2,4}\d{3,4}$', request.module_code.upper()):
        raise HTTPException(400, "Invalid module code format. Use format like ITE301")

    base_score = calculate_base_score(
        request.assignments,
        request.attendance,
        request.engagement,
        request.parental_level,
        request.study_hours
    )

    module_factor = get_module_type_factor(request.module_type)
    credit_factor = min(1.2, request.credit_hours / 3)
    semester_factor = get_semester_type_factor(request.semester_type)

    final_score = base_score * module_factor * credit_factor * semester_factor
    final_score = (final_score * 0.8) + (request.previous_gpa * 0.2)
    final_score = min(4.0, max(0, final_score))

    predicted_grade = numeric_to_grade(final_score)
    scores = [base_score, module_factor * 4, credit_factor * 4]
    confidence = calculate_confidence(scores)

    factors_summary = f"Module: {request.module_code} ({request.module_type}) | Credits: {request.credit_hours} | Assignments: {request.assignments}% | Attendance: {request.attendance}% | Study Hours: {request.study_hours}/week"

    recommendations = generate_recommendations(predicted_grade, [final_score], {
        "assignments": request.assignments,
        "attendance": request.attendance,
        "engagement": request.engagement,
        "study_hours": request.study_hours,
        "parental_level": request.parental_level
    })

    if request.module_type == "core" and final_score < 2.5:
        recommendations = f"⚠️ CORE MODULE ALERT: This is a core course. Focus extra attention. {recommendations}"

    prediction_id = prediction_counter
    prediction_counter += 1

    predictions_db[prediction_id] = {
        "id": prediction_id,
        "user_id": user_id,
        "format": "module",
        "module_code": request.module_code,
        "predicted_grade": predicted_grade,
        "confidence": confidence,
        "input_data": request.dict(),
        "created_at": datetime.utcnow().isoformat()
    }

    return PredictionResponse(
        predicted_grade=predicted_grade,
        grade_description=get_grade_description(predicted_grade),
        grade_category=get_grade_category(predicted_grade),
        confidence=round(confidence, 1),
        recommendations=recommendations,
        factors_summary=factors_summary
    )

# ============================================
# HISTORY ENDPOINTS
# ============================================

@app.get("/api/dashboard/stats")
def dashboard_stats(token: str):
    if token not in tokens_db:
        raise HTTPException(401, "Invalid token")

    user_id = tokens_db[token]
    user_predictions = [p for p in predictions_db.values() if p["user_id"] == user_id]

    return {
        "gpa": 3.45,
        "credits_completed": 72,
        "credits_remaining": 48,
        "courses_enrolled": 5,
        "predictions_count": len(user_predictions)
    }

@app.get("/api/predictions/history")
def prediction_history(token: str):
    if token not in tokens_db:
        raise HTTPException(401, "Invalid token")

    user_id = tokens_db[token]
    user_predictions = [p for p in predictions_db.values() if p["user_id"] == user_id]
    user_predictions.sort(key=lambda x: x["created_at"], reverse=True)

    return user_predictions

@app.get("/api/predictions/recent")
def recent_predictions(token: str):
    if token not in tokens_db:
        raise HTTPException(401, "Invalid token")

    user_id = tokens_db[token]
    user_predictions = [p for p in predictions_db.values() if p["user_id"] == user_id]
    user_predictions.sort(key=lambda x: x["created_at"], reverse=True)

    return [
        {
            "id": p["id"],
            "format": p.get("format", "unknown"),
            "predicted_grade": p["predicted_grade"],
            "confidence": p["confidence"],
            "created_at": p["created_at"]
        }
        for p in user_predictions[:5]
    ]

@app.get("/api/profile")
def get_profile(token: str):
    if token not in tokens_db:
        raise HTTPException(401, "Invalid token")

    user_id = tokens_db[token]
    u = users_db[user_id]
    pred_count = len([p for p in predictions_db.values() if p["user_id"] == user_id])

    return {
        "id": u["id"],
        "username": u["username"],
        "email": u["email"],
        "full_name": u["full_name"],
        "student_id": u["student_id"],
        "created_at": u["created_at"],
        "predictions_count": pred_count
    }

@app.put("/api/profile/update")
def update_profile(request: dict, token: str):
    if token not in tokens_db:
        raise HTTPException(401, "Invalid token")

    user_id = tokens_db[token]

    if "full_name" in request:
        users_db[user_id]["full_name"] = request["full_name"]

    return {"success": True, "message": "Profile updated successfully"}

# ============================================
# LECTURER ENDPOINTS
# ============================================

class LecturerLoginRequest(BaseModel):
    username: str
    password: str
    role: str = "lecturer"

@app.post("/api/lecturer/login")
def lecturer_login(request: LecturerLoginRequest):
    """Login for lecturers"""
    for u in users_db.values():
        if (u.get("role") == "lecturer" and 
            (u["username"] == request.username or u.get("email") == request.username or u.get("lecturer_id") == request.username) and
            verify_password(request.password, u["password_hash"])):
            token = generate_token()
            tokens_db[token] = u["id"]
            return {
                "token": token,
                "user": {
                    "id": u["id"],
                    "username": u["username"],
                    "full_name": u["full_name"],
                    "email": u["email"],
                    "role": "lecturer",
                    "lecturer_id": u.get("lecturer_id", u["username"]),
                    "department": u.get("department", "Information Technology")
                }
            }
    raise HTTPException(401, "Invalid lecturer credentials")

@app.post("/api/lecturer/register")
def lecturer_register(request: dict):
    global user_counter
    
    username = request.get("username") or request.get("lecturer_id")
    email = request.get("email")
    full_name = request.get("full_name")
    lecturer_id = request.get("lecturer_id")
    department = request.get("department", "Information Technology")
    password = request.get("password")
    
    if not username or not email or not full_name or not lecturer_id or not password:
        raise HTTPException(400, "All fields are required")
    
    for u in users_db.values():
        if u.get("username") == username:
            raise HTTPException(400, "Username already taken")
        if u.get("email") == email:
            raise HTTPException(400, "Email already registered")
        if u.get("lecturer_id") == lecturer_id:
            raise HTTPException(400, "Lecturer ID already registered")
    
    user_id = user_counter
    user_counter += 1
    
    users_db[user_id] = {
        "id": user_id,
        "username": username,
        "email": email,
        "full_name": full_name,
        "lecturer_id": lecturer_id,
        "department": department,
        "password_hash": hash_password(password),
        "role": "lecturer",
        "courses": [],
        "created_at": datetime.utcnow().isoformat()
    }
    
    return {
        "success": True,
        "message": "Lecturer registered successfully",
        "user": {
            "id": user_id,
            "username": username,
            "email": email,
            "full_name": full_name,
            "lecturer_id": lecturer_id,
            "department": department,
            "role": "lecturer"
        }
    }

@app.get("/api/lecturer/profile")
def lecturer_profile(token: str):
    if token not in tokens_db:
        raise HTTPException(401, "Invalid token")
    
    user_id = tokens_db[token]
    u = users_db.get(user_id)
    
    if not u or u.get("role") != "lecturer":
        raise HTTPException(403, "Access denied. Lecturer only.")
    
    return {
        "id": u["id"],
        "username": u["username"],
        "full_name": u["full_name"],
        "email": u["email"],
        "lecturer_id": u.get("lecturer_id", u["username"]),
        "department": u.get("department", "Information Technology"),
        "courses": u.get("courses", [])
    }

@app.get("/api/lecturer/courses/manage")
def lecturer_courses_manage(token: str):
    if token not in tokens_db:
        raise HTTPException(401, "Invalid token")
    
    user_id = tokens_db[token]
    u = users_db.get(user_id)
    
    if not u or u.get("role") != "lecturer":
        raise HTTPException(403, "Access denied. Lecturer only.")
    
    lecturer_courses = [c for c in courses_db.values() if c["lecturer_id"] == user_id]
    return lecturer_courses

@app.post("/api/lecturer/courses/create")
def create_course(request: dict, token: str):
    global course_counter
    
    if token not in tokens_db:
        raise HTTPException(401, "Invalid token")
    
    user_id = tokens_db[token]
    u = users_db.get(user_id)
    
    if not u or u.get("role") != "lecturer":
        raise HTTPException(403, "Access denied. Lecturer only.")
    
    course_code = request.get("course_code", "").upper()
    course_name = request.get("course_name")
    credits = request.get("credits", 3)
    capacity = request.get("capacity", 30)
    semester = request.get("semester", "2024/2025")
    
    for c in courses_db.values():
        if c["course_code"] == course_code:
            raise HTTPException(400, f"Course {course_code} already exists")
    
    course_id = course_counter
    course_counter += 1
    
    courses_db[course_id] = {
        "id": course_id,
        "course_code": course_code,
        "course_name": course_name,
        "credits": credits,
        "lecturer_id": user_id,
        "lecturer_name": u.get("full_name", "Lecturer"),
        "department": u.get("department", "Information Technology"),
        "semester": semester,
        "capacity": capacity,
        "enrolled": 0,
        "created_at": datetime.utcnow().isoformat()
    }
    
    if "courses" not in u:
        u["courses"] = []
    u["courses"].append(course_code)
    
    return {
        "success": True,
        "message": f"Course {course_code} created successfully",
        "course": courses_db[course_id]
    }

@app.get("/api/lecturer/courses/{course_id}/students")
def get_course_students(course_id: int, token: str):
    if token not in tokens_db:
        raise HTTPException(401, "Invalid token")
    
    user_id = tokens_db[token]
    u = users_db.get(user_id)
    
    if not u or u.get("role") != "lecturer":
        raise HTTPException(403, "Access denied. Lecturer only.")
    
    course = courses_db.get(course_id)
    if not course or course["lecturer_id"] != user_id:
        raise HTTPException(404, "Course not found")
    
    course_enrollments = [e for e in enrollments_db.values() if e["course_id"] == course_id]
    
    students = []
    for e in course_enrollments:
        student = users_db.get(e["student_id"], {})
        students.append({
            "student_id": student.get("student_id", f"STU{e['student_id']}"),
            "full_name": student.get("full_name", "Unknown"),
            "email": student.get("email", ""),
            "enrolled_at": e["enrolled_at"]
        })
    
    return {
        "course": course,
        "total_students": len(students),
        "students": students
    }

@app.get("/api/lecturer/students")
def lecturer_students(token: str):
    if token not in tokens_db:
        raise HTTPException(401, "Invalid token")
    
    user_id = tokens_db[token]
    u = users_db.get(user_id)
    
    if not u or u.get("role") != "lecturer":
        raise HTTPException(403, "Access denied. Lecturer only.")
    
    lecturer_courses = u.get("courses", [])
    course_predictions = [p for p in predictions_db.values() if p.get("course_code") in lecturer_courses]
    
    student_data = {}
    for p in course_predictions:
        student_id = p["user_id"]
        if student_id not in student_data:
            student = users_db.get(student_id, {})
            student_data[student_id] = {
                "student_id": student.get("student_id", f"STU{student_id}"),
                "full_name": student.get("full_name", f"Student {student_id}"),
                "latest_grade": p["predicted_grade"],
                "confidence": p["confidence"],
                "course_code": p.get("course_code"),
                "last_active": p["created_at"]
            }
    
    result = []
    for s in student_data.values():
        grade = s["latest_grade"]
        if grade in ['D', 'F', 'D+']:
            risk = "high"
        elif grade in ['C', 'C+', 'C-']:
            risk = "medium"
        else:
            risk = "low"
        
        result.append({
            "student_id": s["student_id"],
            "full_name": s["full_name"],
            "course_code": s["course_code"],
            "latest_grade": s["latest_grade"],
            "confidence": s["confidence"],
            "risk_level": risk,
            "last_active": s["last_active"]
        })
    
    return result

@app.get("/api/lecturer/alerts")
def lecturer_alerts(token: str):
    if token not in tokens_db:
        raise HTTPException(401, "Invalid token")
    
    user_id = tokens_db[token]
    u = users_db.get(user_id)
    
    if not u or u.get("role") != "lecturer":
        raise HTTPException(403, "Access denied. Lecturer only.")
    
    lecturer_courses = u.get("courses", [])
    at_risk_predictions = [
        p for p in predictions_db.values() 
        if p.get("course_code") in lecturer_courses and p.get("predicted_grade") in ['D', 'F', 'D+']
    ]
    
    result = []
    for p in at_risk_predictions:
        student = users_db.get(p["user_id"], {})
        result.append({
            "student_id": student.get("student_id", f"STU{p['user_id']}"),
            "student_name": student.get("full_name", f"Student {p['user_id']}"),
            "course_code": p.get("course_code"),
            "predicted_grade": p["predicted_grade"],
            "confidence": p["confidence"],
            "risk_level": "high" if p["predicted_grade"] in ['F'] else "medium",
            "recommendation": "Immediate academic intervention recommended" if p["predicted_grade"] == 'F' else "Monitor progress, consider additional support"
        })
    
    return result

# ============================================
# STUDENT COURSE ENDPOINTS
# ============================================

@app.get("/api/student/courses/available")
def get_available_courses(token: str):
    if token not in tokens_db:
        raise HTTPException(401, "Invalid token")
    
    user_id = tokens_db[token]
    student = users_db.get(user_id)
    
    if not student or student.get("role") != "student":
        raise HTTPException(403, "Access denied. Students only.")
    
    student_enrollments = [e["course_id"] for e in enrollments_db.values() if e["student_id"] == user_id]
    
    available_courses = []
    for c in courses_db.values():
        if c["id"] not in student_enrollments and c["enrolled"] < c["capacity"]:
            available_courses.append({
                "id": c["id"],
                "course_code": c["course_code"],
                "course_name": c["course_name"],
                "credits": c["credits"],
                "lecturer_name": c["lecturer_name"],
                "capacity": c["capacity"],
                "available_spots": c["capacity"] - c["enrolled"],
                "semester": c["semester"]
            })
    
    return available_courses

@app.get("/api/student/courses/my-courses")
def get_my_courses(token: str):
    if token not in tokens_db:
        raise HTTPException(401, "Invalid token")
    
    user_id = tokens_db[token]
    student = users_db.get(user_id)
    
    if not student or student.get("role") != "student":
        raise HTTPException(403, "Access denied. Students only.")
    
    my_enrollments = [e for e in enrollments_db.values() if e["student_id"] == user_id]
    
    my_courses = []
    for e in my_enrollments:
        course = courses_db.get(e["course_id"])
        if course:
            my_courses.append({
                "id": course["id"],
                "course_code": course["course_code"],
                "course_name": course["course_name"],
                "credits": course["credits"],
                "lecturer_name": course["lecturer_name"],
                "enrolled_at": e["enrolled_at"],
                "status": e.get("status", "active")
            })
    
    return my_courses

@app.post("/api/student/courses/enroll")
def enroll_course(request: dict, token: str):
    global enrollment_counter
    
    if token not in tokens_db:
        raise HTTPException(401, "Invalid token")
    
    user_id = tokens_db[token]
    student = users_db.get(user_id)
    
    if not student or student.get("role") != "student":
        raise HTTPException(403, "Access denied. Students only.")
    
    course_id = request.get("course_id")
    course = courses_db.get(course_id)
    
    if not course:
        raise HTTPException(404, "Course not found")
    
    existing = [e for e in enrollments_db.values() if e["student_id"] == user_id and e["course_id"] == course_id]
    if existing:
        raise HTTPException(400, "Already enrolled in this course")
    
    if course["enrolled"] >= course["capacity"]:
        raise HTTPException(400, "Course is full")
    
    enrollment_id = enrollment_counter
    enrollment_counter += 1
    
    enrollments_db[enrollment_id] = {
        "id": enrollment_id,
        "student_id": user_id,
        "course_id": course_id,
        "course_code": course["course_code"],
        "enrolled_at": datetime.utcnow().isoformat(),
        "status": "active"
    }
    
    courses_db[course_id]["enrolled"] += 1
    
    return {
        "success": True,
        "message": f"Successfully enrolled in {course['course_code']}",
        "enrollment": enrollments_db[enrollment_id]
    }

@app.delete("/api/student/courses/drop/{course_id}")
def drop_course(course_id: int, token: str):
    if token not in tokens_db:
        raise HTTPException(401, "Invalid token")
    
    user_id = tokens_db[token]
    student = users_db.get(user_id)
    
    if not student or student.get("role") != "student":
        raise HTTPException(403, "Access denied. Students only.")
    
    enrollment = None
    for e in enrollments_db.values():
        if e["student_id"] == user_id and e["course_id"] == course_id:
            enrollment = e
            break
    
    if not enrollment:
        raise HTTPException(404, "Not enrolled in this course")
    
    del enrollments_db[enrollment["id"]]
    
    if course_id in courses_db:
        courses_db[course_id]["enrolled"] -= 1
    
    return {"success": True, "message": "Course dropped successfully"}

# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)




@app.get("/api/debug/enrollments")
def debug_enrollments(token: str):
    """Debug endpoint to check enrollments"""
    if token not in tokens_db:
        return {"error": "Invalid token"}
    
    user_id = tokens_db[token]
    user = users_db.get(user_id)
    
    if not user or user.get("role") != "lecturer":
        return {"error": "Lecturer access required"}
    
    all_enrollments = []
    for e in enrollments_db.values():
        course = courses_db.get(e["course_id"], {})
        student = users_db.get(e["student_id"], {})
        all_enrollments.append({
            "enrollment_id": e["id"],
            "course_code": e.get("course_code"),
            "student_id": student.get("student_id"),
            "student_name": student.get("full_name"),
            "student_email": student.get("email"),
            "enrolled_at": e["enrolled_at"]
        })
    
    return {
        "total_enrollments": len(all_enrollments),
        "enrollments": all_enrollments
    }

@app.get("/api/debug/users")
def debug_users(admin_key: str):
    """Debug endpoint to see all users"""
    if admin_key != "DEBUG2024":
        raise HTTPException(403, "Invalid key")
    
    users_list = []
    for uid, u in users_db.items():
        users_list.append({
            "id": uid,
            "username": u.get("username"),
            "full_name": u.get("full_name"),
            "email": u.get("email"),
            "student_id": u.get("student_id"),
            "role": u.get("role")
        })
    
    return {
        "total_users": len(users_list),
        "users": users_list
    }
