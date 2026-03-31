"""
USTED Student Self-Assessment Predictor - Complete Backend API
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
import re
import secrets
import hashlib
from datetime import datetime

# ============================================
# DATA STORAGE (In-memory)
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

def predict_grade_simple(current_grade, study_hours, difficulty, confidence):
    grade_value = grade_to_numeric(current_grade)
    study_boost = min(0.5, study_hours / 80)
    confidence_boost = (confidence - 3) * 0.1
    difficulty_penalty = (difficulty - 3) * 0.1
    
    final_score = grade_value + study_boost + confidence_boost - difficulty_penalty
    final_score = max(0, min(4.0, final_score))
    
    conf_score = 70 + (study_hours / 2) + (confidence * 5) - (difficulty * 5)
    conf_score = max(50, min(95, conf_score))
    
    return numeric_to_grade(final_score), conf_score

def get_recommendations(grade):
    recs = {
        'A': "Excellent! Keep up your great study habits.",
        'B+': "Very good. Focus on challenging topics.",
        'B': "Good. Review difficult concepts.",
        'C+': "Satisfactory. Increase study time.",
        'C': "Consider attending tutorials.",
        'D+': "Meet with your academic advisor.",
        'D': "Urgent: Contact your advisor.",
        'F': "Immediate intervention needed."
    }
    return recs.get(grade, "Keep working hard!")

# ============================================
# PYDANTIC MODELS
# ============================================

class UserCreate(BaseModel):
    username: str
    full_name: str
    email: str
    student_id: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class PredictionRequest(BaseModel):
    course_code: str
    current_grade: str
    semester: int
    academic_year: int
    study_hours: int = 10
    difficulty: int = 3
    confidence: int = 3

# ============================================
# FASTAPI APP
# ============================================

app = FastAPI(title="USTED Predictor API", version="2.0")

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
    return {"message": "USTED Predictor API is running", "status": "active"}

@app.get("/api/health")
def health():
    return {
        "status": "healthy", 
        "users": len(users_db), 
        "predictions": len(predictions_db),
        "tokens": len(tokens_db)
    }

@app.post("/api/register")
def register(user: UserCreate):
    global user_counter
    
    if not re.match(r'^[A-Z]{3}\d{5,7}$', user.student_id.upper()):
        raise HTTPException(400, "Student ID must be 3 letters + 5-7 digits")
    
    for u in users_db.values():
        if u["username"] == user.username:
            raise HTTPException(400, "Username already taken")
        if u["email"] == user.email:
            raise HTTPException(400, "Email already registered")
        if u["student_id"] == user.student_id.upper():
            raise HTTPException(400, "Student ID already registered")
    
    user_id = user_counter
    user_counter += 1
    
    users_db[user_id] = {
        "id": user_id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "student_id": user.student_id.upper(),
        "password_hash": hash_password(user.password),
        "created_at": datetime.utcnow().isoformat()
    }
    
    return {
        "id": user_id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "student_id": user.student_id.upper()
    }

@app.post("/api/login")
def login(request: LoginRequest):
    for u in users_db.values():
        if u["username"] == request.username and verify_password(request.password, u["password_hash"]):
            token = generate_token()
            tokens_db[token] = u["id"]
            return {
                "token": token,
                "user": {
                    "id": u["id"],
                    "username": u["username"],
                    "email": u["email"],
                    "full_name": u["full_name"],
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
            "email": u["email"],
            "full_name": u["full_name"],
            "student_id": u["student_id"]
        }
    raise HTTPException(401, "Invalid token")

# ============================================
# PREDICTION ENDPOINTS
# ============================================

@app.post("/api/predict")
def predict(request: PredictionRequest, token: str):
    global prediction_counter
    
    if token not in tokens_db:
        raise HTTPException(401, "Invalid token")
    
    user_id = tokens_db[token]
    
    if not re.match(r'^[A-Z]{2,4}\d{3,4}$', request.course_code.upper()):
        raise HTTPException(400, "Invalid course code format")
    
    predicted_grade, confidence = predict_grade_simple(
        request.current_grade,
        request.study_hours,
        request.difficulty,
        request.confidence
    )
    
    prediction_id = prediction_counter
    prediction_counter += 1
    
    predictions_db[prediction_id] = {
        "id": prediction_id,
        "user_id": user_id,
        "course_code": request.course_code.upper(),
        "predicted_grade": predicted_grade,
        "confidence": confidence,
        "actual_grade": None,
        "created_at": datetime.utcnow().isoformat()
    }
    
    return {
        "predicted_grade": predicted_grade,
        "confidence": round(confidence, 1),
        "recommendations": get_recommendations(predicted_grade),
        "prediction_id": prediction_id
    }

# ============================================
# DASHBOARD ENDPOINTS
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

@app.get("/api/profile")
def get_profile(token: str):
    if token not in tokens_db:
        raise HTTPException(401, "Invalid token")
    
    user_id = tokens_db[token]
    u = users_db.get(user_id)
    
    if not u:
        raise HTTPException(404, "User not found")
    
    pred_count = len([p for p in predictions_db.values() if p["user_id"] == user_id])
    
    return {
        "id": u["id"],
        "username": u["username"],
        "email": u["email"],
        "full_name": u["full_name"],
        "student_id": u["student_id"],
        "created_at": u.get("created_at", datetime.utcnow().isoformat()),
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
            "course_code": p["course_code"],
            "predicted_grade": p["predicted_grade"],
            "confidence": p["confidence"],
            "created_at": p["created_at"]
        }
        for p in user_predictions[:5]
    ]

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
