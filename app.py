"""
USTED Student Self-Assessment Predictor - Backend API
Simplified version - No ML dependencies
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import os
import re

# ============================================
# CONFIGURATION
# ============================================

SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# In-memory database (for demo - replace with real DB later)
users_db = {}
predictions_db = {}
user_counter = 1
prediction_counter = 1

# ============================================
# PYDANTIC MODELS
# ============================================

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    student_id: str
    password: str
    
    @validator('student_id')
    def validate_student_id(cls, v):
        if not re.match(r'^[A-Z]{3}\d{5,7}$', v.upper()):
            raise ValueError('Student ID must be 3 letters followed by 5-7 digits')
        return v.upper()

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    student_id: str
    created_at: datetime
    role: str = "student"

class Token(BaseModel):
    access_token: str
    token_type: str

class PredictionRequest(BaseModel):
    course_code: str
    current_grade: str
    semester: int
    academic_year: int
    study_hours: int = 10
    difficulty: int = 3
    confidence: int = 3
    
    @validator('course_code')
    def validate_course_code(cls, v):
        if not re.match(r'^[A-Z]{2,4}\d{3,4}$', v.upper()):
            raise ValueError('Course code must be 2-4 letters followed by 3-4 digits')
        return v.upper()

class PredictionResponse(BaseModel):
    predicted_grade: str
    confidence: float
    recommendations: str

class DashboardStats(BaseModel):
    gpa: float
    credits_completed: int
    credits_remaining: int
    courses_enrolled: int

# ============================================
# UTILITY FUNCTIONS
# ============================================

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

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

def predict_grade(current_grade, study_hours, difficulty, confidence):
    """Simple prediction logic"""
    grade_value = grade_to_numeric(current_grade)
    
    # Adjust based on inputs
    study_boost = min(0.5, study_hours / 80)
    confidence_boost = (confidence - 3) * 0.1
    difficulty_penalty = (difficulty - 3) * 0.1
    
    final_score = grade_value + study_boost + confidence_boost - difficulty_penalty
    final_score = max(0, min(4.0, final_score))
    
    # Calculate confidence
    conf_score = 70 + (study_hours / 2) + (confidence * 5) - (difficulty * 5)
    conf_score = max(50, min(95, conf_score))
    
    return numeric_to_grade(final_score), conf_score

def generate_recommendations(grade, confidence):
    if grade == 'A':
        return "Excellent! Keep up your great study habits."
    elif grade == 'B+':
        return "Very good performance. Focus on challenging topics."
    elif grade == 'B':
        return "Good performance. Review difficult concepts."
    elif grade == 'C+':
        return "Satisfactory. Increase study time."
    elif grade == 'C':
        return "You may need additional support. Attend tutorials."
    elif grade == 'D+':
        return "Below average. Meet with your academic advisor."
    elif grade == 'D':
        return "Poor performance. Urgent action needed."
    else:
        return "Failing. Contact your academic advisor immediately."

# ============================================
# FASTAPI APP
# ============================================

app = FastAPI(
    title="USTED Student Predictor API",
    description="API for student self-assessment and performance prediction",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# API ENDPOINTS
# ============================================

@app.get("/")
def root():
    return {"message": "USTED Predictor API is running", "status": "active"}

@app.get("/api/health")
def health_check():
    return {"status": "healthy"}

@app.post("/api/register", response_model=UserResponse)
def register(user: UserCreate):
    global user_counter
    
    # Check if user exists
    for existing in users_db.values():
        if existing["username"] == user.username:
            raise HTTPException(status_code=400, detail="Username already registered")
        if existing["email"] == user.email:
            raise HTTPException(status_code=400, detail="Email already registered")
        if existing["student_id"] == user.student_id:
            raise HTTPException(status_code=400, detail="Student ID already registered")
    
    # Create new user
    user_id = user_counter
    user_counter += 1
    
    new_user = {
        "id": user_id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "student_id": user.student_id,
        "hashed_password": get_password_hash(user.password),
        "created_at": datetime.utcnow(),
        "role": "student"
    }
    
    users_db[user_id] = new_user
    
    return UserResponse(
        id=user_id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        student_id=user.student_id,
        created_at=new_user["created_at"],
        role="student"
    )

@app.post("/api/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Find user by username
    user = None
    for u in users_db.values():
        if u["username"] == form_data.username:
            user = u
            break
    
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/verify", response_model=UserResponse)
def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Find user
    for user in users_db.values():
        if user["username"] == username:
            return UserResponse(
                id=user["id"],
                username=user["username"],
                email=user["email"],
                full_name=user["full_name"],
                student_id=user["student_id"],
                created_at=user["created_at"],
                role=user["role"]
            )
    
    raise HTTPException(status_code=404, detail="User not found")

@app.post("/api/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest, token: str = Depends(oauth2_scheme)):
    # Verify token (simplified)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Make prediction
    predicted_grade, confidence = predict_grade(
        request.current_grade,
        request.study_hours,
        request.difficulty,
        request.confidence
    )
    
    # Save prediction (in-memory)
    global prediction_counter
    predictions_db[prediction_counter] = {
        "id": prediction_counter,
        "username": username,
        "course_code": request.course_code,
        "predicted_grade": predicted_grade,
        "confidence": confidence,
        "created_at": datetime.utcnow()
    }
    prediction_counter += 1
    
    recommendations = generate_recommendations(predicted_grade, confidence)
    
    return PredictionResponse(
        predicted_grade=predicted_grade,
        confidence=round(confidence, 1),
        recommendations=recommendations
    )

@app.get("/api/dashboard/stats", response_model=DashboardStats)
def dashboard_stats(token: str = Depends(oauth2_scheme)):
    return DashboardStats(
        gpa=3.45,
        credits_completed=72,
        credits_remaining=48,
        courses_enrolled=5
    )

@app.get("/api/predictions/history")
def prediction_history(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_predictions = [p for p in predictions_db.values() if p["username"] == username]
    user_predictions.reverse()
    
    return [
        {
            "id": p["id"],
            "course_code": p["course_code"],
            "predicted_grade": p["predicted_grade"],
            "confidence": p["confidence"],
            "actual_grade": None,
            "created_at": p["created_at"]
        }
        for p in user_predictions
    ]

@app.get("/api/predictions/recent")
def recent_predictions(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_predictions = [p for p in predictions_db.values() if p["username"] == username]
    user_predictions.reverse()
    
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

@app.get("/api/profile")
def get_profile(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    for user in users_db.values():
        if user["username"] == username:
            predictions_count = len([p for p in predictions_db.values() if p["username"] == username])
            return {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "full_name": user["full_name"],
                "student_id": user["student_id"],
                "created_at": user["created_at"],
                "predictions_count": predictions_count
            }
    
    raise HTTPException(status_code=404, detail="User not found")

@app.put("/api/profile/update")
def update_profile(request: dict, token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    for user_id, user in users_db.items():
        if user["username"] == username:
            if "full_name" in request:
                users_db[user_id]["full_name"] = request["full_name"]
            return {"success": True, "message": "Profile updated successfully"}
    
    raise HTTPException(status_code=404, detail="User not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
