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
        'A': 'Excellent',
        'A-': 'Excellent',
        'B+': 'Very Good',
        'B': 'Good',
        'B-': 'Good',
        'C+': 'Average',
        'C': 'Average',
        'C-': 'Average',
        'D+': 'Poor',
        'D': 'Poor',
        'F': 'Failing'
    }
    return categories.get(grade, 'Unknown')

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

def get_parental_factor(parental_level):
    """Convert parental education level to factor (0-1 scale)"""
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
        recommendations.append("📝 IMPROVE ASSIGNMENTS: Complete all assignments on time. They carry significant weight.")
    
    if factors.get("attendance", 75) < 80:
        recommendations.append("📅 BOOST ATTENDANCE: Regular attendance is crucial for understanding course material.")
    
    if factors.get("engagement", 65) < 70:
        recommendations.append("💬 INCREASE ENGAGEMENT: Participate in class discussions and ask questions.")
    
    if factors.get("study_hours", 10) < 15:
        recommendations.append(f"⏰ STUDY MORE: Current {factors.get('study_hours', 10)} hrs/week. Aim for 15-20 hrs per course.")
    
    if factors.get("parental_level", "secondary") in ["none", "primary"]:
        recommendations.append("👨‍👩‍👧 SEEK SUPPORT: Discuss your academic goals with family for encouragement.")
    
    if not recommendations:
        recommendations.append("🌟 EXCELLENT! You're on track. Maintain consistency and consider helping peers.")
    
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
    
    # Semester progression factor (later semesters are harder)
    progression_factor = 1 - ((request.current_semester - 1) / request.total_semesters) * 0.15
    
    # Final score
    final_score = base_score * semester_factor * progression_factor
    
    # Adjust with previous GPA (20% influence)
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
    
    # Week progression factor (mid-semester pressure)
    week_factor = 1 - ((request.week_number - 1) / request.total_weeks) * 0.1
    
    # Consistency factor
    consistency_factor = 0.9 + (request.consistency / 100) * 0.1
    
    # Semester type influence
    semester_factor = get_semester_type_factor(request.semester_type)
    
    # Final score
    final_score = base_score * week_factor * consistency_factor * semester_factor
    
    # Adjust with previous GPA
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
        recommendations = f"📊 IMPROVE CONSISTENCY: Your consistency score is {request.consistency}%. Aim for steady weekly effort. | {recommendations}"
    
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
    
    # Adjust with previous GPA
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




