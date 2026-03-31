"""
USTED Complete Academic Predictor - All Formats
Includes: Semester, Weekly, and Module formats
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import re
import secrets
import hashlib
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

# ============================================
# FORMAT CALCULATIONS
# ============================================

def calculate_semester_factor(semester_type, current_semester, total_semesters=8):
    """Calculate factor based on semester format"""
    factors = {
        "regular": 1.0,
        "non-regular": 0.92,  # Non-regular is slightly more challenging
        "modular": 0.88,      # Modular courses are intensive
        "sandwich": 0.95,     # Work-study combination
        "distance": 0.85      # Distance learning needs more self-discipline
    }
    
    base_factor = factors.get(semester_type.lower(), 1.0)
    
    # Progress factor - later semesters are harder
    progress_factor = 1 - (current_semester / total_semesters) * 0.15
    
    return base_factor * progress_factor

def calculate_weekly_factor(attendance, assignments, study_hours, tutorial_attendance=0):
    """Calculate factor based on weekly performance"""
    # Attendance factor (0-100%)
    attendance_factor = attendance / 100
    
    # Assignments factor (0-100%)
    assignments_factor = assignments / 100
    
    # Study hours factor (0-40 hours)
    study_factor = min(1.0, study_hours / 25)
    
    # Tutorial attendance factor (optional)
    tutorial_factor = tutorial_attendance / 100 if tutorial_attendance > 0 else 0.7
    
    # Weighted average
    weekly_score = (
        attendance_factor * 0.25 +
        assignments_factor * 0.35 +
        study_factor * 0.30 +
        tutorial_factor * 0.10
    )
    
    return weekly_score

def calculate_module_factor(module_data):
    """Calculate factor based on module-specific performance"""
    # Module credit hours impact
    credit_factor = min(1.2, module_data.get("credit_hours", 3) / 3)
    
    # Previous module grades impact
    previous_grades = module_data.get("previous_grades", [])
    if previous_grades:
        avg_previous = sum(grade_to_numeric(g) for g in previous_grades) / len(previous_grades)
        previous_factor = avg_previous / 4.0
    else:
        previous_factor = 0.7
    
    # Module difficulty (1-5 scale)
    difficulty_factor = 1 - (module_data.get("difficulty", 3) - 3) * 0.1
    
    # Module type impact (core, elective, project)
    module_type_factors = {
        "core": 0.95,      # Core courses are harder
        "elective": 1.05,   # Electives are often easier
        "project": 0.90,    # Projects require more effort
        "lab": 0.92         # Labs need practical skills
    }
    type_factor = module_type_factors.get(module_data.get("module_type", "core"), 1.0)
    
    return (credit_factor + previous_factor + difficulty_factor + type_factor) / 4

def calculate_parental_factor(parent_education, parent_support=3):
    """Calculate factor based on parental education and support"""
    education_factors = {
        "none": 0.7,
        "primary": 0.8,
        "secondary": 0.9,
        "tertiary": 1.0,
        "postgraduate": 1.1
    }
    edu_factor = education_factors.get(parent_education.lower(), 0.9)
    
    # Parental support (1-5 scale)
    support_factor = 0.8 + (parent_support / 5) * 0.4
    
    return (edu_factor + support_factor) / 2

def predict_complete_grade(data):
    """Complete prediction using all factors"""
    
    # 1. Base from previous grades (25%)
    previous_gpa = data.get("previous_gpa", 3.0)
    base_score = grade_to_numeric(previous_gpa)
    
    # 2. Semester format factor (15%)
    semester_factor = calculate_semester_factor(
        data.get("semester_type", "regular"),
        data.get("current_semester", 3)
    )
    
    # 3. Weekly performance factor (20%)
    weekly_factor = calculate_weekly_factor(
        data.get("attendance", 75),
        data.get("assignments", 70),
        data.get("study_hours", 12),
        data.get("tutorial_attendance", 50)
    )
    
    # 4. Module format factor (15%)
    module_factor = calculate_module_factor({
        "credit_hours": data.get("credit_hours", 3),
        "previous_grades": data.get("previous_course_grades", []),
        "difficulty": data.get("difficulty", 3),
        "module_type": data.get("module_type", "core")
    })
    
    # 5. Parental education factor (10%)
    parent_factor = calculate_parental_factor(
        data.get("parental_education", "secondary"),
        data.get("parental_support", 3)
    )
    
    # 6. Self-assessment factor (15%)
    self_factor = (data.get("self_confidence", 3) + data.get("perceived_readiness", 3)) / 10
    
    # Calculate final score
    final_score = (
        base_score * 0.25 +
        semester_factor * 4.0 * 0.15 +
        weekly_factor * 4.0 * 0.20 +
        module_factor * 4.0 * 0.15 +
        parent_factor * 0.10 +
        self_factor * 4.0 * 0.15
    )
    
    final_score = min(4.0, max(0, final_score))
    
    # Calculate confidence based on data completeness
    confidence = 50 + (weekly_factor * 20) + (module_factor * 15) + (self_factor * 15)
    confidence = min(95, max(50, confidence))
    
    return numeric_to_grade(final_score), round(confidence, 1)

# ============================================
# PYDANTIC MODELS
# ============================================

class WeeklyData(BaseModel):
    attendance: int = Field(75, ge=0, le=100, description="Attendance percentage")
    assignments: int = Field(70, ge=0, le=100, description="Assignment submission/completion percentage")
    study_hours: int = Field(12, ge=0, le=40, description="Weekly study hours")
    tutorial_attendance: int = Field(50, ge=0, le=100, description="Tutorial attendance percentage")

class ModuleData(BaseModel):
    module_code: str
    credit_hours: int = Field(3, ge=1, le=6)
    module_type: str = Field("core", description="core, elective, project, lab")
    difficulty: int = Field(3, ge=1, le=5)
    previous_grades: Optional[List[str]] = Field([], description="Grades from related modules")

class SemesterData(BaseModel):
    semester_type: str = Field("regular", description="regular, non-regular, modular, sandwich, distance")
    current_semester: int = Field(1, ge=1, le=8)
    total_semesters: int = Field(8, ge=4, le=12)

class ParentalData(BaseModel):
    education: str = Field("secondary", description="none, primary, secondary, tertiary, postgraduate")
    support_level: int = Field(3, ge=1, le=5, description="Parental support level 1-5")

class CompletePredictionRequest(BaseModel):
    # Student Info
    student_name: str
    student_id: str
    
    # Previous Performance
    previous_gpa: float = Field(3.0, ge=0, le=4.0)
    previous_course_grades: Optional[List[str]] = []
    
    # Semester Format
    semester: SemesterData
    
    # Weekly Format
    weekly: WeeklyData
    
    # Module Format
    module: ModuleData
    
    # Parental Background
    parental: ParentalData
    
    # Self Assessment
    self_confidence: int = Field(3, ge=1, le=5)
    perceived_readiness: int = Field(3, ge=1, le=5)

# ============================================
# FASTAPI APP
# ============================================

app = FastAPI(title="USTED Complete Predictor API", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# ENDPOINTS
# ============================================

@app.get("/")
def root():
    return {"message": "USTED Complete Predictor API is running", "version": "3.0"}

@app.post("/api/register")
def register(user: dict):
    global user_counter
    # Simple registration for now
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

@app.post("/api/predict-complete")
def predict_complete(request: CompletePredictionRequest, token: str):
    global prediction_counter
    
    if token not in tokens_db:
        raise HTTPException(401, "Invalid token")
    
    user_id = tokens_db[token]
    
    # Prepare data for prediction
    prediction_data = {
        "previous_gpa": request.previous_gpa,
        "previous_course_grades": request.previous_course_grades,
        "semester_type": request.semester.semester_type,
        "current_semester": request.semester.current_semester,
        "attendance": request.weekly.attendance,
        "assignments": request.weekly.assignments,
        "study_hours": request.weekly.study_hours,
        "tutorial_attendance": request.weekly.tutorial_attendance,
        "credit_hours": request.module.credit_hours,
        "module_type": request.module.module_type,
        "difficulty": request.module.difficulty,
        "parental_education": request.parental.education,
        "parental_support": request.parental.support_level,
        "self_confidence": request.self_confidence,
        "perceived_readiness": request.perceived_readiness
    }
    
    # Make prediction
    predicted_grade, confidence = predict_complete_grade(prediction_data)
    
    # Calculate all factors for display
    semester_factor = calculate_semester_factor(request.semester.semester_type, request.semester.current_semester)
    weekly_score = calculate_weekly_factor(
        request.weekly.attendance,
        request.weekly.assignments,
        request.weekly.study_hours,
        request.weekly.tutorial_attendance
    )
    module_factor = calculate_module_factor({
        "credit_hours": request.module.credit_hours,
        "previous_grades": request.previous_course_grades,
        "difficulty": request.module.difficulty,
        "module_type": request.module.module_type
    })
    parent_factor = calculate_parental_factor(request.parental.education, request.parental.support_level)
    
    # Generate detailed recommendations
    recommendations = generate_detailed_recommendations(
        predicted_grade, confidence,
        weekly_score, module_factor,
        request.weekly.study_hours,
        request.weekly.attendance,
        request.weekly.assignments
    )
    
    # Save prediction
    prediction_id = prediction_counter
    prediction_counter += 1
    
    predictions_db[prediction_id] = {
        "id": prediction_id,
        "user_id": user_id,
        "course_code": request.module.module_code,
        "predicted_grade": predicted_grade,
        "confidence": confidence,
        "input_data": prediction_data,
        "actual_grade": None,
        "created_at": datetime.utcnow().isoformat()
    }
    
    return {
        "predicted_grade": predicted_grade,
        "confidence": confidence,
        "recommendations": recommendations,
        "factors_analysis": {
            "semester_factor": round(semester_factor, 2),
            "weekly_performance": round(weekly_score * 100, 1),
            "module_factor": round(module_factor, 2),
            "parental_factor": round(parent_factor, 2),
            "previous_gpa": request.previous_gpa,
            "study_hours": request.weekly.study_hours,
            "attendance": request.weekly.attendance,
            "assignments": request.weekly.assignments
        },
        "prediction_id": prediction_id
    }

def generate_detailed_recommendations(grade, confidence, weekly_score, module_factor, study_hours, attendance, assignments):
    recommendations = []
    
    # Grade-based recommendations
    if grade in ['D', 'F']:
        recommendations.append("🚨 CRITICAL: Schedule immediate meeting with academic advisor")
    
    # Study hours recommendations
    if study_hours < 15:
        recommendations.append(f"📚 INCREASE STUDY HOURS: Currently {study_hours}/week. Aim for 20-25 hours per course")
    elif study_hours > 30:
        recommendations.append("⚠️ Monitor burnout risk. Ensure quality over quantity")
    
    # Attendance recommendations
    if attendance < 80:
        recommendations.append("📅 IMPROVE ATTENDANCE: Missing lectures affects understanding. Aim for 90%+")
    
    # Assignments recommendations
    if assignments < 70:
        recommendations.append("📝 COMPLETE ASSIGNMENTS: Submit all assignments on time for better understanding")
    
    # Weekly performance
    if weekly_score < 0.6:
        recommendations.append("📊 IMPROVE WEEKLY ENGAGEMENT: Participate actively in tutorials and lab sessions")
    
    # Module-specific
    if module_factor < 0.7:
        recommendations.append("📖 MODULE PREPARATION: Review prerequisites and strengthen foundation")
    
    if not recommendations:
        recommendations.append("🌟 EXCELLENT PROGRESS! Maintain consistency and consider helping peers")
    
    return " | ".join(recommendations)

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
