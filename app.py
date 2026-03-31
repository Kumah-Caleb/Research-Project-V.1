"""
USTED Student Self-Assessment Predictor - Enhanced Backend API
With Calendar Semester, Weekly Format, and Parental Education
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
import re
import secrets
import hashlib
from datetime import datetime, timedelta
import json

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
    grade_map = {'A': 4.0, 'B+': 3.5, 'B': 3.0, 'C+': 2.5, 
                 'C': 2.0, 'D+': 1.5, 'D': 1.0, 'F': 0.0}
    return grade_map.get(grade, 2.0)

def numeric_to_grade(value):
    if value >= 3.5: return 'A'
    if value >= 3.0: return 'B+'
    if value >= 2.5: return 'B'
    if value >= 2.0: return 'C+'
    if value >= 1.5: return 'C'
    if value >= 1.0: return 'D+'
    if value >= 0.5: return 'D'
    return 'F'

def get_parental_education_weight(education_level):
    """Convert parental education to weight factor"""
    weights = {
        "none": 0.5,
        "primary": 0.7,
        "secondary": 0.85,
        "tertiary": 1.0,
        "postgraduate": 1.15
    }
    return weights.get(education_level.lower(), 0.85)

def calculate_weekly_score(weekly_data):
    """Calculate weekly performance score"""
    score = 0
    if weekly_data.get("assignments_submitted", 0) >= 80:
        score += 30
    elif weekly_data.get("assignments_submitted", 0) >= 60:
        score += 20
    else:
        score += 10
    
    if weekly_data.get("attendance", 0) >= 90:
        score += 30
    elif weekly_data.get("attendance", 0) >= 75:
        score += 20
    else:
        score += 10
    
    if weekly_data.get("quiz_scores", 0) >= 80:
        score += 40
    elif weekly_data.get("quiz_scores", 0) >= 60:
        score += 25
    else:
        score += 15
    
    return score

def predict_grade_enhanced(data):
    """Enhanced prediction with all new features"""
    
    # Base grade from current performance
    grade_value = grade_to_numeric(data.get("current_grade", "C"))
    
    # Study hours factor (0-40 hours)
    study_hours = min(40, max(0, data.get("study_hours", 10)))
    study_factor = study_hours / 40  # 0 to 1
    
    # Weekly performance factor
    weekly_score = calculate_weekly_score(data.get("weekly_data", {}))
    weekly_factor = weekly_score / 100  # 0 to 1
    
    # Overall assessment (quiz + assignment + midterm)
    overall_score = data.get("overall_score", 50)
    overall_factor = overall_score / 100
    
    # Parental education factor
    parent_education = data.get("parental_education", "secondary")
    parent_factor = get_parental_education_weight(parent_education)
    
    # Semester type factor (Regular vs Non-Regular)
    semester_type = data.get("semester_type", "regular")
    semester_factor = 1.0 if semester_type == "regular" else 0.95  # Non-regular slightly harder
    
    # Calculate final score
    final_score = (
        grade_value * 0.25 +
        study_factor * 4.0 * 0.15 +
        weekly_factor * 4.0 * 0.20 +
        overall_factor * 4.0 * 0.20 +
        parent_factor * 0.10 +
        semester_factor * 0.10
    )
    
    final_score = min(4.0, max(0, final_score))
    
    # Calculate confidence based on data completeness
    confidence = 60 + (study_hours / 2) + (weekly_score / 5) + (overall_score / 10)
    confidence = min(95, max(50, confidence))
    
    return numeric_to_grade(final_score), round(confidence, 1)

def get_detailed_recommendations(grade, study_hours, weekly_score, overall_score):
    """Generate detailed recommendations based on all factors"""
    recommendations = []
    
    if grade in ['D', 'F']:
        recommendations.append("🚨 URGENT: Schedule meeting with academic advisor immediately")
    
    if study_hours < 15:
        recommendations.append(f"📚 Increase study hours (currently {study_hours}/week). Aim for 15-20 hours per course")
    
    if weekly_score < 60:
        recommendations.append("📝 Improve weekly engagement: submit assignments on time and attend all classes")
    
    if overall_score < 60:
        recommendations.append("📊 Focus on improving quiz and mid-term scores. Review weak areas")
    
    if grade in ['A', 'B+']:
        recommendations.append("🌟 Excellent work! Consider helping peers and exploring advanced topics")
    elif grade in ['B', 'C+']:
        recommendations.append("📖 Good progress. Focus on challenging topics and maintain consistency")
    
    if not recommendations:
        recommendations.append("👍 Keep up the good work! Consistency is key to success")
    
    return " | ".join(recommendations)

# ============================================
# PYDANTIC MODELS
# ============================================

class WeeklyData(BaseModel):
    assignments_submitted: int = Field(0, ge=0, le=100, description="Percentage of assignments submitted")
    attendance: int = Field(0, ge=0, le=100, description="Attendance percentage")
    quiz_scores: int = Field(0, ge=0, le=100, description="Average quiz scores")

class EnhancedPredictionRequest(BaseModel):
    # Basic info
    course_code: str
    current_grade: str
    semester_type: str = "regular"  # regular, non-regular
    
    # Calendar semester info
    semester: int = Field(1, ge=1, le=8)
    academic_year: int
    
    # Weekly format
    weekly_data: WeeklyData
    
    # Overall assessment
    overall_score: int = Field(50, ge=0, le=100, description="Overall performance score (0-100)")
    
    # Study hours
    study_hours: int = Field(10, ge=0, le=40, description="Weekly study hours")
    
    # Parental education
    parental_education: str = "secondary"  # none, primary, secondary, tertiary, postgraduate
    
    # Additional factors
    difficulty: int = Field(3, ge=1, le=5)
    confidence: int = Field(3, ge=1, le=5)

class EnhancedPredictionResponse(BaseModel):
    predicted_grade: str
    confidence: float
    recommendations: str
    factors_analysis: dict

# ============================================
# FASTAPI APP
# ============================================

app = FastAPI(title="USTED Enhanced Predictor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# EXISTING ENDPOINTS (keep from previous)
# ============================================

@app.get("/")
def root():
    return {"message": "USTED Enhanced Predictor API is running", "version": "2.0"}

@app.post("/api/register")
def register(user: dict):
    global user_counter
    # ... (same as before)
    return {"id": 1, "username": user.get("username")}

@app.post("/api/login")
def login(request: dict):
    # ... (same as before)
    return {"token": "fake-token", "user": {}}

@app.get("/api/verify")
def verify(token: str):
    # ... (same as before)
    return {"id": 1, "username": "test"}

# ============================================
# NEW ENHANCED PREDICTION ENDPOINT
# ============================================

@app.post("/api/predict-enhanced", response_model=EnhancedPredictionResponse)
def predict_enhanced(request: EnhancedPredictionRequest, token: str):
    global prediction_counter
    
    # Verify token
    if token not in tokens_db:
        raise HTTPException(401, "Invalid token")
    
    user_id = tokens_db[token]
    
    # Validate course code
    if not re.match(r'^[A-Z]{2,4}\d{3,4}$', request.course_code.upper()):
        raise HTTPException(400, "Invalid course code format")
    
    # Prepare data for prediction
    prediction_data = {
        "current_grade": request.current_grade,
        "study_hours": request.study_hours,
        "weekly_data": request.weekly_data.dict(),
        "overall_score": request.overall_score,
        "parental_education": request.parental_education,
        "semester_type": request.semester_type,
        "difficulty": request.difficulty,
        "confidence": request.confidence
    }
    
    # Make enhanced prediction
    predicted_grade, confidence = predict_grade_enhanced(prediction_data)
    
    # Calculate factor contributions for analysis
    weekly_score = calculate_weekly_score(request.weekly_data.dict())
    parent_factor = get_parental_education_weight(request.parental_education)
    
    factors_analysis = {
        "study_hours_factor": f"{request.study_hours}/40 hours ({int(request.study_hours/40*100)}%)",
        "weekly_engagement": f"{weekly_score}/100",
        "overall_assessment": f"{request.overall_score}/100",
        "parental_education": f"{request.parental_education} (impact: {parent_factor})",
        "semester_type": request.semester_type
    }
    
    # Generate detailed recommendations
    recommendations = get_detailed_recommendations(
        predicted_grade, 
        request.study_hours, 
        weekly_score,
        request.overall_score
    )
    
    # Save prediction
    prediction_id = prediction_counter
    prediction_counter += 1
    
    predictions_db[prediction_id] = {
        "id": prediction_id,
        "user_id": user_id,
        "course_code": request.course_code.upper(),
        "predicted_grade": predicted_grade,
        "confidence": confidence,
        "input_data": prediction_data,
        "actual_grade": None,
        "created_at": datetime.utcnow().isoformat()
    }
    
    return EnhancedPredictionResponse(
        predicted_grade=predicted_grade,
        confidence=confidence,
        recommendations=recommendations,
        factors_analysis=factors_analysis
    )

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
