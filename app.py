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
user_counter = 1
prediction_counter = 1

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
    """Return description based on USTED grading system"""
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
    """Return category based on USTED grading system"""
    categories = {
        'A': 'Excellent', 'A-': 'Excellent',
        'B+': 'Very Good', 'B': 'Good', 'B-': 'Good',
        'C+': 'Average', 'C': 'Average', 'C-': 'Average',
        'D+': 'Poor', 'D': 'Poor',
        'F': 'Failing'
    }
    return categories.get(grade, 'Unknown')

def get_parental_factor(parental_level):
    """Convert parental education level to factor"""
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
    """Calculate base score from core factors (0-4 scale)"""
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
    """Calculate confidence based on data consistency"""
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
        "created_at": datetime.utcnow().isoformat()
    }
    return {"id": user_id, "username": user.get("username")}

@app.post("/api/login")
def login(request: dict):
    username = request.get("username")
    password = request.get("password")

    for u in users_db.values():
        if u["username"] == username and verify_password(password, u["password_hash"]):
            token = generate_token()
            tokens_db[token] = u["id"]
            return {
                "token": token,
                "user": {
                    "id": u["id"],
                    "username": u["username"],
                    "full_name": u["full_name"],
                    "email": u["email"],
                    "student_id": u["student_id"]
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
# SEMESTER FORMAT PREDICTION
# ============================================

@app.post("/api/predict-semester", response_model=PredictionResponse)
def predict_semester(request: SemesterPredictionRequest, token: str):
    global prediction_counter

    if token not in tokens_db:
        raise HTTPException(401, "Invalid token")

    user_id = tokens_db[token]

    # Calculate base score
    base_score = calculate_base_score(
        request.assignments,
        request.attendance,
        request.engagement,
        request.parental_level,
        request.study_hours
    )

    # Semester type factor
    semester_factor = get_semester_type_factor(request.semester_type)

    # Semester progression factor
    progression_factor = 1 - ((request.current_semester - 1) / request.total_semesters) * 0.15

    # Final score
    final_score = base_score * semester_factor * progression_factor
    final_score = (final_score * 0.8) + (request.previous_gpa * 0.2)
    final_score = min(4.0, max(0, final_score))

    predicted_grade = numeric_to_grade(final_score)

    # Calculate confidence
    scores = [base_score, semester_factor * 4, progression_factor * 4]
    confidence = calculate_confidence(scores)

    # Factors summary
    factors_summary = f"Semester: {request.semester_type} | Assignments: {request.assignments}% | Attendance: {request.attendance}% | Engagement: {request.engagement}% | Study Hours: {request.study_hours}/week"

    # Recommendations
    recommendations = generate_recommendations(predicted_grade, [final_score], {
        "assignments": request.assignments,
        "attendance": request.attendance,
        "engagement": request.engagement,
        "study_hours": request.study_hours,
        "parental_level": request.parental_level
    })

    # Save prediction
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

# ============================================
# WEEKLY FORMAT PREDICTION
# ============================================

@app.post("/api/predict-weekly", response_model=PredictionResponse)
def predict_weekly(request: WeeklyPredictionRequest, token: str):
    global prediction_counter

    if token not in tokens_db:
        raise HTTPException(401, "Invalid token")

    user_id = tokens_db[token]

    # Calculate base score
    base_score = calculate_base_score(
        request.assignments,
        request.attendance,
        request.engagement,
        request.parental_level,
        request.study_hours
    )

    # Week progression factor
    week_factor = 1 - ((request.week_number - 1) / request.total_weeks) * 0.1

    # Consistency factor
    consistency_factor = 0.9 + (request.consistency / 100) * 0.1

    # Semester type influence
    semester_factor = get_semester_type_factor(request.semester_type)

    # Final score
    final_score = base_score * week_factor * consistency_factor * semester_factor
    final_score = (final_score * 0.8) + (request.previous_gpa * 0.2)
    final_score = min(4.0, max(0, final_score))

    predicted_grade = numeric_to_grade(final_score)

    # Calculate confidence
    scores = [base_score, week_factor * 4, consistency_factor * 4]
    confidence = calculate_confidence(scores)

    # Factors summary
    factors_summary = f"Week {request.week_number}/{request.total_weeks} | Consistency: {request.consistency}% | Assignments: {request.assignments}% | Attendance: {request.attendance}% | Study Hours: {request.study_hours}/week"

    # Recommendations
    recommendations = generate_recommendations(predicted_grade, [final_score], {
        "assignments": request.assignments,
        "attendance": request.attendance,
        "engagement": request.engagement,
        "study_hours": request.study_hours,
        "parental_level": request.parental_level
    })

    # Add weekly-specific recommendation
    if request.consistency < 70:
        recommendations = f"📊 IMPROVE CONSISTENCY: Your consistency score is {request.consistency}%. | {recommendations}"

    # Save prediction
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

# ============================================
# MODULE FORMAT PREDICTION
# ============================================

@app.post("/api/predict-module", response_model=PredictionResponse)
def predict_module(request: ModulePredictionRequest, token: str):
    global prediction_counter

    if token not in tokens_db:
        raise HTTPException(401, "Invalid token")

    user_id = tokens_db[token]

    # Validate module code format
    if request.module_code and not re.match(r'^[A-Z]{2,4}\d{3,4}$', request.module_code.upper()):
        raise HTTPException(400, "Invalid module code format. Use format like ITE301")

    # Calculate base score
    base_score = calculate_base_score(
        request.assignments,
        request.attendance,
        request.engagement,
        request.parental_level,
        request.study_hours
    )

    # Module type factor
    module_factor = get_module_type_factor(request.module_type)

    # Credit hours factor
    credit_factor = min(1.2, request.credit_hours / 3)

    # Semester type factor
    semester_factor = get_semester_type_factor(request.semester_type)

    # Final score
    final_score = base_score * module_factor * credit_factor * semester_factor
    final_score = (final_score * 0.8) + (request.previous_gpa * 0.2)
    final_score = min(4.0, max(0, final_score))

    predicted_grade = numeric_to_grade(final_score)

    # Calculate confidence
    scores = [base_score, module_factor * 4, credit_factor * 4]
    confidence = calculate_confidence(scores)

    # Factors summary
    factors_summary = f"Module: {request.module_code} ({request.module_type}) | Credits: {request.credit_hours} | Assignments: {request.assignments}% | Attendance: {request.attendance}% | Study Hours: {request.study_hours}/week"

    # Recommendations
    recommendations = generate_recommendations(predicted_grade, [final_score], {
        "assignments": request.assignments,
        "attendance": request.attendance,
        "engagement": request.engagement,
        "study_hours": request.study_hours,
        "parental_level": request.parental_level
    })

    # Add module-specific recommendation
    if request.module_type == "core" and final_score < 2.5:
        recommendations = f"⚠️ CORE MODULE ALERT: This is a core course. Focus extra attention. {recommendations}"

    # Save prediction
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# ============================================
# LECTURER ENDPOINTS
# ============================================

class LecturerLoginRequest(BaseModel):
    username: str
    password: str
    role: str = "lecturer"

class LecturerProfile(BaseModel):
    id: int
    username: str
    full_name: str
    email: str
    department: str
    courses: List[str] = []

@app.post("/api/lecturer/login")
def lecturer_login(request: LecturerLoginRequest):
    """Login for lecturers"""
    # For demo, create a default lecturer
    lecturer_id = 1001
    if request.username == "lecturer" or request.username == "dr.smith":
        token = generate_token()
        tokens_db[token] = lecturer_id
        # Store lecturer info
        users_db[lecturer_id] = {
            "id": lecturer_id,
            "username": request.username,
            "full_name": "Dr. John Smith",
            "email": "john.smith@usted.edu.gh",
            "department": "Information Technology",
            "role": "lecturer",
            "courses": ["ITE301", "ITE302", "ITE303"]
        }
        return {
            "token": token,
            "user": {
                "id": lecturer_id,
                "username": request.username,
                "full_name": "Dr. John Smith",
                "email": "john.smith@usted.edu.gh",
                "role": "lecturer"
            }
        }
    raise HTTPException(401, "Invalid lecturer credentials")

@app.get("/api/lecturer/profile")
def lecturer_profile(token: str):
    """Get lecturer profile"""
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
        "department": u.get("department", "Information Technology"),
        "courses": u.get("courses", [])
    }

@app.get("/api/lecturer/stats")
def lecturer_stats(token: str):
    """Get overall statistics for lecturer's courses"""
    if token not in tokens_db:
        raise HTTPException(401, "Invalid token")
    
    user_id = tokens_db[token]
    u = users_db.get(user_id)
    
    if not u or u.get("role") != "lecturer":
        raise HTTPException(403, "Access denied. Lecturer only.")
    
    lecturer_courses = u.get("courses", [])
    
    # Get all predictions for courses taught by this lecturer
    course_predictions = [p for p in predictions_db.values() if p.get("course_code") in lecturer_courses]
    
    # Get all students who made predictions in these courses
    student_ids = set(p["user_id"] for p in course_predictions)
    
    # Calculate stats
    total_students = len(student_ids)
    at_risk_count = len([p for p in course_predictions if p.get("predicted_grade") in ['D', 'F', 'D+']])
    avg_grades = [grade_to_numeric(p.get("predicted_grade", 'C')) for p in course_predictions]
    avg_gpa = sum(avg_grades) / len(avg_grades) if avg_grades else 0
    
    return {
        "total_students": total_students,
        "at_risk_count": at_risk_count,
        "avg_predicted_gpa": round(avg_gpa, 2),
        "total_predictions": len(course_predictions)
    }

@app.get("/api/lecturer/students")
def lecturer_students(token: str):
    """Get all students in lecturer's courses with their latest predictions"""
    if token not in tokens_db:
        raise HTTPException(401, "Invalid token")
    
    user_id = tokens_db[token]
    u = users_db.get(user_id)
    
    if not u or u.get("role") != "lecturer":
        raise HTTPException(403, "Access denied. Lecturer only.")
    
    lecturer_courses = u.get("courses", [])
    
    # Get all predictions for lecturer's courses
    course_predictions = [p for p in predictions_db.values() if p.get("course_code") in lecturer_courses]
    
    # Group by student
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
        else:
            # Update if this prediction is newer
            if p["created_at"] > student_data[student_id]["last_active"]:
                student_data[student_id]["latest_grade"] = p["predicted_grade"]
                student_data[student_id]["confidence"] = p["confidence"]
                student_data[student_id]["last_active"] = p["created_at"]
    
    # Calculate risk level
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

@app.get("/api/lecturer/courses")
def lecturer_courses(token: str):
    """Get all courses taught by lecturer with statistics"""
    if token not in tokens_db:
        raise HTTPException(401, "Invalid token")
    
    user_id = tokens_db[token]
    u = users_db.get(user_id)
    
    if not u or u.get("role") != "lecturer":
        raise HTTPException(403, "Access denied. Lecturer only.")
    
    lecturer_courses = u.get("courses", [])
    
    result = []
    for course in lecturer_courses:
        course_predictions = [p for p in predictions_db.values() if p.get("course_code") == course]
        student_ids = set(p["user_id"] for p in course_predictions)
        at_risk = len([p for p in course_predictions if p.get("predicted_grade") in ['D', 'F', 'D+']])
        avg_grades = [grade_to_numeric(p.get("predicted_grade", 'C')) for p in course_predictions]
        avg_grade = sum(avg_grades) / len(avg_grades) if avg_grades else 0
        avg_letter = numeric_to_grade(avg_grade)
        
        result.append({
            "course_code": course,
            "course_name": f"Advanced {course}",
            "student_count": len(student_ids),
            "avg_grade": avg_letter,
            "at_risk_count": at_risk
        })
    
    return result

@app.get("/api/lecturer/alerts")
def lecturer_alerts(token: str):
    """Get at-risk students that need attention"""
    if token not in tokens_db:
        raise HTTPException(401, "Invalid token")
    
    user_id = tokens_db[token]
    u = users_db.get(user_id)
    
    if not u or u.get("role") != "lecturer":
        raise HTTPException(403, "Access denied. Lecturer only.")
    
    lecturer_courses = u.get("courses", [])
    
    # Get at-risk predictions
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

@app.get("/api/lecturer/analytics")
def lecturer_analytics(token: str):
    """Get analytics data for charts"""
    if token not in tokens_db:
        raise HTTPException(401, "Invalid token")
    
    user_id = tokens_db[token]
    u = users_db.get(user_id)
    
    if not u or u.get("role") != "lecturer":
        raise HTTPException(403, "Access denied. Lecturer only.")
    
    lecturer_courses = u.get("courses", [])
    course_predictions = [p for p in predictions_db.values() if p.get("course_code") in lecturer_courses]
    
    # Grade distribution
    grade_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
    for p in course_predictions:
        grade = p["predicted_grade"]
        if grade.startswith('A'):
            grade_counts["A"] += 1
        elif grade.startswith('B'):
            grade_counts["B"] += 1
        elif grade.startswith('C'):
            grade_counts["C"] += 1
        elif grade.startswith('D'):
            grade_counts["D"] += 1
        else:
            grade_counts["F"] += 1
    
    # Risk distribution
    risk_counts = {"low": 0, "medium": 0, "high": 0}
    for p in course_predictions:
        grade = p["predicted_grade"]
        if grade in ['A', 'B', 'B+', 'B-']:
            risk_counts["low"] += 1
        elif grade in ['C', 'C+', 'C-']:
            risk_counts["medium"] += 1
        else:
            risk_counts["high"] += 1
    
    return {
        "grade_a": grade_counts["A"],
        "grade_b": grade_counts["B"],
        "grade_c": grade_counts["C"],
        "grade_d": grade_counts["D"],
        "grade_f": grade_counts["F"],
        "low_risk": risk_counts["low"],
        "medium_risk": risk_counts["medium"],
        "high_risk": risk_counts["high"],
        "weeks": ["Week 1", "Week 2", "Week 3", "Week 4"],
        "trend_data": [3.2, 3.1, 3.3, 3.4]
    }

@app.post("/api/lecturer/predict-student")
def lecturer_predict_student(request: dict, token: str):
    """Lecturer predicts performance for a specific student"""
    if token not in tokens_db:
        raise HTTPException(401, "Invalid token")
    
    user_id = tokens_db[token]
    u = users_db.get(user_id)
    
    if not u or u.get("role") != "lecturer":
        raise HTTPException(403, "Access denied. Lecturer only.")
    
    # Calculate prediction using existing logic
    grade_value = grade_to_numeric(request.get("current_grade", "C"))
    study_hours = min(40, max(0, request.get("study_hours", 10)))
    attendance = request.get("attendance", 75) / 100
    assignments = request.get("assignments", 70) / 100
    parental_factor = get_parental_factor(request.get("parental_level", "secondary"))
    study_factor = min(1.0, study_hours / 25)
    
    final_score = (grade_value * 0.25 + study_factor * 4.0 * 0.15 + assignments * 4.0 * 0.25 + attendance * 4.0 * 0.25 + parental_factor * 0.10)
    final_score = min(4.0, max(0, final_score))
    predicted_grade = numeric_to_grade(final_score)
    confidence = 50 + (study_hours / 2) + (attendance * 20) + (assignments * 20)
    confidence = min(95, max(50, confidence))
    
    recommendations = f"Student: {request.get('student_id')} - Keep improving study habits. Current study hours: {study_hours}/week"
    
    return {
        "predicted_grade": predicted_grade,
        "confidence": round(confidence, 1),
        "grade_description": get_grade_description(predicted_grade),
        "recommendations": recommendations
    }

@app.get("/api/student/predict/data")
def get_student_predict_data(student_id: str, token: str):
    """Get student data for prediction (placeholder)"""
    if token not in tokens_db:
        raise HTTPException(401, "Invalid token")
    
    return {
        "course_code": "ITE301",
        "semester": 3,
        "study_hours": 12,
        "attendance": 80,
        "assignments": 75
    }
