"""
USTED Complete Academic Predictor - Three Format System
Each format has: Assignments, Attendance, Engagement, Parental Level, Study Hours, Extracurricular (from calendar)
Semester Type influences Weekly Format
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
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
# PARENTAL LEVEL FACTORS
# ============================================

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

# ============================================
# EXTRACURRICULAR CALENDAR
# ============================================

# Academic calendar events that count as extracurricular activities
EXTRACURRICULAR_TYPES = {
    "sports": "Sports competitions, matches, tournaments",
    "cultural": "Cultural festivals, drama, music performances",
    "academic_clubs": "Academic clubs, debates, quiz competitions",
    "volunteering": "Community service, volunteering events",
    "leadership": "Student leadership roles, committee work",
    "workshops": "Workshops, seminars, conferences",
    "hackathons": "Hackathons, coding competitions",
    "research": "Research projects, presentations"
}

def calculate_extracurricular_factor(events_count, event_types, event_hours):
    """Calculate factor based on extracurricular activities during academic calendar"""
    # Base factor - moderate extracurricular is good, too many or too few is bad
    if events_count == 0:
        base_factor = 0.7  # No extracurricular = less holistic development
    elif events_count <= 3:
        base_factor = 0.9  # Balanced extracurricular
    elif events_count <= 6:
        base_factor = 1.0  # Optimal extracurricular involvement
    elif events_count <= 10:
        base_factor = 0.85  # Too many events - may affect studies
    else:
        base_factor = 0.7   # Overwhelming extracurricular
    
    # Type diversity factor
    unique_types = len(set(event_types))
    diversity_factor = 0.8 + (unique_types / len(EXTRACURRICULAR_TYPES)) * 0.3
    diversity_factor = min(1.0, diversity_factor)
    
    # Hours factor (5-15 hours per week is optimal)
    if event_hours == 0:
        hours_factor = 0.7
    elif event_hours <= 5:
        hours_factor = 0.85
    elif event_hours <= 10:
        hours_factor = 1.0
    elif event_hours <= 15:
        hours_factor = 0.9
    else:
        hours_factor = 0.75
    
    return (base_factor + diversity_factor + hours_factor) / 3

# ============================================
# FORMAT CALCULATIONS
# ============================================

def calculate_factor_score(assignments, attendance, engagement, parental_level, study_hours, extracurricular):
    """Calculate score from individual factors (0-4 scale)"""
    
    # Assignments factor (0-100%)
    assignments_factor = assignments / 100
    
    # Attendance factor (0-100%)
    attendance_factor = attendance / 100
    
    # Engagement factor (0-100%)
    engagement_factor = engagement / 100
    
    # Parental level factor
    parental_factor = get_parental_factor(parental_level)
    
    # Study hours factor (0-40 hours, optimal 20-25)
    if study_hours == 0:
        study_factor = 0.4
    elif study_hours <= 10:
        study_factor = 0.6
    elif study_hours <= 15:
        study_factor = 0.8
    elif study_hours <= 25:
        study_factor = 1.0
    elif study_hours <= 35:
        study_factor = 0.85
    else:
        study_factor = 0.7
    
    # Extracurricular factor (from calendar events)
    extracurricular_factor = extracurricular.get("factor", 0.8)
    
    # Weighted calculation (0-1 scale)
    score = (
        assignments_factor * 0.25 +
        attendance_factor * 0.20 +
        engagement_factor * 0.20 +
        parental_factor * 0.15 +
        study_factor * 0.15 +
        extracurricular_factor * 0.05
    )
    
    return score * 4.0

def get_semester_type_factor(semester_type):
    """Get factor for different semester types"""
    factors = {
        "regular": 1.0,
        "non-regular": 0.92,
        "modular": 0.88,
        "sandwich": 0.95,
        "distance": 0.85
    }
    return factors.get(semester_type.lower(), 1.0)

def calculate_semester_format(data, extracurricular_data):
    """Calculate semester format score"""
    base_score = calculate_factor_score(
        data.assignments,
        data.attendance,
        data.engagement,
        data.parental_level,
        data.study_hours,
        extracurricular_data
    )
    
    # Semester type adjustment
    type_factor = get_semester_type_factor(data.semester_type)
    
    # Semester progression (later semesters harder)
    progression_factor = 1 - ((data.current_semester - 1) / data.total_semesters) * 0.15
    
    return base_score * type_factor * progression_factor

def calculate_weekly_format(data, semester_type_factor, extracurricular_data):
    """Calculate weekly format score - influenced by semester type"""
    base_score = calculate_factor_score(
        data.assignments,
        data.attendance,
        data.engagement,
        data.parental_level,
        data.study_hours,
        extracurricular_data
    )
    
    # Week progression factor (mid-semester pressure)
    week_factor = 1 - ((data.week_number - 1) / data.total_weeks) * 0.1
    
    # Consistency factor (how consistent is the student)
    consistency_factor = 0.9 + (data.consistency / 100) * 0.1
    
    # Semester type influence on weekly workload
    semester_influence = semester_type_factor
    
    return base_score * week_factor * consistency_factor * semester_influence

def calculate_module_format(data, extracurricular_data):
    """Calculate module format score"""
    base_score = calculate_factor_score(
        data.assignments,
        data.attendance,
        data.engagement,
        data.parental_level,
        data.study_hours,
        extracurricular_data
    )
    
    # Module type adjustment
    type_factors = {"core": 0.95, "elective": 1.05, "project": 0.90, "lab": 0.92}
    type_factor = type_factors.get(data.module_type.lower(), 1.0)
    
    # Credit hours impact
    credit_factor = min(1.2, data.credit_hours / 3)
    
    return base_score * type_factor * credit_factor

# ============================================
# PYDANTIC MODELS
# ============================================

class ExtracurricularActivities(BaseModel):
    events_count: int = Field(3, ge=0, le=20, description="Number of extracurricular events participated in")
    event_types: List[str] = Field(["academic_clubs"], description="Types of events: sports, cultural, academic_clubs, volunteering, leadership, workshops, hackathons, research")
    event_hours_per_week: int = Field(5, ge=0, le=30, description="Average hours per week on extracurricular")

class SemesterFormat(BaseModel):
    semester_type: str = Field("regular", description="regular, non-regular, modular, sandwich, distance")
    current_semester: int = Field(3, ge=1, le=12)
    total_semesters: int = Field(8, ge=4, le=12)
    assignments: int = Field(75, ge=0, le=100, description="Semester assignments completion %")
    attendance: int = Field(80, ge=0, le=100, description="Semester attendance %")
    engagement: int = Field(70, ge=0, le=100, description="Semester engagement %")
    parental_level: str = Field("secondary", description="none, primary, secondary, tertiary, postgraduate")
    study_hours: int = Field(12, ge=0, le=40, description="Weekly study hours")

class WeeklyFormat(BaseModel):
    week_number: int = Field(8, ge=1, le=16)
    total_weeks: int = Field(16, ge=12, le=20)
    assignments: int = Field(70, ge=0, le=100, description="Weekly assignments submission %")
    attendance: int = Field(75, ge=0, le=100, description="Weekly attendance %")
    engagement: int = Field(65, ge=0, le=100, description="Weekly engagement %")
    parental_level: str = Field("secondary", description="Parental education level")
    study_hours: int = Field(10, ge=0, le=40, description="Weekly study hours")
    consistency: int = Field(70, ge=0, le=100, description="Weekly consistency score")

class ModuleFormat(BaseModel):
    module_code: str = Field("ITE301", description="Module code")
    module_type: str = Field("core", description="core, elective, project, lab")
    credit_hours: int = Field(3, ge=1, le=6)
    assignments: int = Field(80, ge=0, le=100, description="Module assignments completion %")
    attendance: int = Field(85, ge=0, le=100, description="Module attendance %")
    engagement: int = Field(75, ge=0, le=100, description="Module engagement %")
    parental_level: str = Field("secondary", description="Parental education level")
    study_hours: int = Field(8, ge=0, le=40, description="Study hours for this module")

class CompletePredictionRequest(BaseModel):
    semester: SemesterFormat
    weekly: WeeklyFormat
    module: ModuleFormat
    extracurricular: ExtracurricularActivities
    previous_gpa: float = Field(3.0, ge=0, le=4.0)

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
# PREDICTION ENDPOINT
# ============================================

@app.post("/api/predict-three-format")
def predict_three_format(request: CompletePredictionRequest, token: str):
    global prediction_counter
    
    if token not in tokens_db:
        raise HTTPException(401, "Invalid token")
    
    user_id = tokens_db[token]
    
    # Calculate extracurricular factor
    extracurricular_factor = calculate_extracurricular_factor(
        request.extracurricular.events_count,
        request.extracurricular.event_types,
        request.extracurricular.event_hours_per_week
    )
    
    extracurricular_data = {
        "factor": extracurricular_factor,
        "events_count": request.extracurricular.events_count,
        "event_types": request.extracurricular.event_types,
        "hours_per_week": request.extracurricular.event_hours_per_week
    }
    
    # Calculate semester format score
    semester_type_factor = get_semester_type_factor(request.semester.semester_type)
    semester_score = calculate_semester_format(request.semester, extracurricular_data)
    
    # Calculate weekly format score (influenced by semester type)
    weekly_score = calculate_weekly_format(request.weekly, semester_type_factor, extracurricular_data)
    
    # Calculate module format score
    module_score = calculate_module_format(request.module, extracurricular_data)
    
    # Combine all three formats with weights
    # Semester: 40%, Weekly: 30%, Module: 30%
    final_score = (semester_score * 0.4) + (weekly_score * 0.3) + (module_score * 0.3)
    
    # Adjust with previous GPA (20% influence)
    final_score = (final_score * 0.8) + (request.previous_gpa * 0.2)
    
    final_score = min(4.0, max(0, final_score))
    predicted_grade = numeric_to_grade(final_score)
    
    # Calculate confidence based on data completeness
    confidence = 50 + (semester_score / 4.0 * 20) + (weekly_score / 4.0 * 15) + (module_score / 4.0 * 15)
    confidence = min(95, max(50, confidence))
    
    # Save prediction
    prediction_id = prediction_counter
    prediction_counter += 1
    
    predictions_db[prediction_id] = {
        "id": prediction_id,
        "user_id": user_id,
        "course_code": request.module.module_code,
        "predicted_grade": predicted_grade,
        "confidence": round(confidence, 1),
        "semester_score": round(semester_score, 2),
        "weekly_score": round(weekly_score, 2),
        "module_score": round(module_score, 2),
        "extracurricular_factor": round(extracurricular_factor, 2),
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Generate recommendations
    recommendations = generate_recommendations(
        predicted_grade, semester_score, weekly_score, module_score,
        request.semester, request.weekly, request.module, extracurricular_data
    )
    
    return {
        "predicted_grade": predicted_grade,
        "confidence": round(confidence, 1),
        "scores": {
            "semester_format": round(semester_score, 2),
            "weekly_format": round(weekly_score, 2),
            "module_format": round(module_score, 2)
        },
        "extracurricular": {
            "factor": round(extracurricular_factor, 2),
            "events_count": request.extracurricular.events_count,
            "event_types": request.extracurricular.event_types,
            "hours_per_week": request.extracurricular.event_hours_per_week
        },
        "recommendations": recommendations,
        "prediction_id": prediction_id
    }

def generate_recommendations(grade, semester_score, weekly_score, module_score, semester, weekly, module, extracurricular):
    recs = []
    
    # Grade-based
    if grade in ['D', 'F']:
        recs.append("🚨 URGENT: Schedule meeting with academic advisor immediately")
    
    # Semester format recommendations
    if semester_score < 2.5:
        recs.append(f"📚 IMPROVE SEMESTER PERFORMANCE: Increase study hours ({semester.study_hours}/week recommended: 20-25)")
        if semester.attendance < 80:
            recs.append("📅 BOOST ATTENDANCE: Current semester attendance is low. Aim for 85%+")
        if semester.assignments < 75:
            recs.append("📝 COMPLETE ASSIGNMENTS: Submit all semester assignments on time")
    
    # Weekly format recommendations
    if weekly_score < 2.5:
        recs.append(f"⏰ IMPROVE WEEKLY CONSISTENCY: Current consistency score {weekly.consistency}%")
        if weekly.attendance < 80:
            recs.append("📆 WEEKLY ATTENDANCE: Attend all lectures this week")
    
    # Module format recommendations
    if module_score < 2.5:
        recs.append(f"📖 FOCUS ON MODULE: Spend more time on {module.module_code}")
        if module.study_hours < 10:
            recs.append(f"⏱️ INCREASE MODULE STUDY TIME: Currently {module.study_hours}hrs/week, aim for 12-15")
    
    # Extracurricular recommendations
    if extracurricular["events_count"] > 8:
        recs.append("⚖️ BALANCE EXTRACURRICULARS: Too many activities may affect studies. Consider reducing to 3-5 events")
    elif extracurricular["events_count"] == 0:
        recs.append("🌟 GET INVOLVED: Join academic clubs or participate in extracurricular activities for holistic development")
    
    # Parental level recommendations
    if semester.parental_level == "none" or semester.parental_level == "primary":
        recs.append("👨‍👩‍👧 SEEK SUPPORT: Discuss your academic goals with family for encouragement")
    
    if not recs:
        recs.append("🌟 EXCELLENT! Maintain your current strategy. You're on track for success!")
    
    return " | ".join(recs)

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
