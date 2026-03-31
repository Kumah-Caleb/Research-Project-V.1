"""
USTED Student Self-Assessment Predictor - Backend API
AAMUSTED Project
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os
import joblib
import numpy as np
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================
# CONFIGURATION
# ============================================

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Database URL (Render PostgreSQL or local SQLite)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./usted_predictor.db")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# ============================================
# DATABASE SETUP
# ============================================

# For SQLite
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ============================================
# DATABASE MODELS
# ============================================

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    student_id = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    role = Column(String, default="student")

class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    course_code = Column(String)
    predicted_grade = Column(String)
    confidence_score = Column(Float)
    input_data = Column(JSON)
    actual_grade = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

# ============================================
# PYDANTIC MODELS (Request/Response)
# ============================================

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    student_id: str
    password: str
    
    @validator('student_id')
    def validate_student_id(cls, v):
        import re
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
    role: str
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

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
        import re
        if not re.match(r'^[A-Z]{2,4}\d{3,4}$', v.upper()):
            raise ValueError('Course code must be 2-4 letters followed by 3-4 digits')
        return v.upper()
    
    @validator('semester')
    def validate_semester(cls, v):
        if v < 1 or v > 8:
            raise ValueError('Semester must be between 1 and 8')
        return v
    
    @validator('academic_year')
    def validate_year(cls, v):
        if v < 2000 or v > 2030:
            raise ValueError('Academic year must be between 2000 and 2030')
        return v

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

def get_user(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_user_by_student_id(db: Session, student_id: str):
    return db.query(User).filter(User.student_id == student_id).first()

def authenticate_user(db: Session, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# ============================================
# LOAD MACHINE LEARNING MODEL
# ============================================

# Try to load trained model, if not available, use a simple fallback
try:
    model = joblib.load('model.pkl')
    model_available = True
except:
    model_available = False
    print("Warning: Model file not found. Using fallback predictions.")

def predict_grade(course_code, current_grade, semester, study_hours, difficulty, confidence):
    """Predict grade based on inputs"""
    
    if model_available:
        try:
            # Prepare features for model
            features = np.array([[
                grade_to_numeric(current_grade),
                semester,
                study_hours,
                difficulty,
                confidence
            ]])
            
            prediction = model.predict(features)[0]
            probability = model.predict_proba(features)[0].max() if hasattr(model, 'predict_proba') else 0.85
            
            return numeric_to_grade(prediction), probability * 100
        except:
            pass
    
    # Fallback prediction logic (simple rules)
    grade_value = grade_to_numeric(current_grade)
    
    # Adjust based on study hours
    study_boost = min(0.5, study_hours / 80)
    
    # Adjust based on confidence and difficulty
    confidence_boost = (confidence - 3) * 0.1
    difficulty_penalty = (difficulty - 3) * 0.1
    
    final_score = grade_value + study_boost + confidence_boost - difficulty_penalty
    final_score = max(0, min(4.0, final_score))
    
    # Calculate confidence
    confidence_score = 70 + (study_hours / 2) + (confidence * 5) - (difficulty * 5)
    confidence_score = max(50, min(95, confidence_score))
    
    return numeric_to_grade(final_score), confidence_score

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

# ============================================
# FASTAPI APP
# ============================================

app = FastAPI(
    title="USTED Student Predictor API",
    description="API for student self-assessment and performance prediction",
    version="1.0.0"
)

# CORS middleware - allow frontend to call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your frontend URL
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
    return {"status": "healthy", "model_available": model_available}

@app.post("/api/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(lambda: SessionLocal())):
    # Check if user exists
    if get_user(db, user.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    if get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if get_user_by_student_id(db, user.student_id):
        raise HTTPException(status_code=400, detail="Student ID already registered")
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        student_id=user.student_id.upper(),
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@app.post("/api/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(lambda: SessionLocal())):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/verify", response_model=UserResponse)
def verify_token(token: str = Depends(oauth2_scheme), db: Session = Depends(lambda: SessionLocal())):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = get_user(db, username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

@app.post("/api/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest, token: str = Depends(oauth2_scheme), db: Session = Depends(lambda: SessionLocal())):
    # Verify user
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = get_user(db, username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Make prediction
    predicted_grade, confidence = predict_grade(
        request.course_code,
        request.current_grade,
        request.semester,
        request.study_hours,
        request.difficulty,
        request.confidence
    )
    
    # Save prediction to database
    prediction = Prediction(
        user_id=user.id,
        course_code=request.course_code,
        predicted_grade=predicted_grade,
        confidence_score=confidence,
        input_data=request.dict()
    )
    db.add(prediction)
    db.commit()
    
    # Generate recommendations
    recommendations = generate_recommendations(predicted_grade, confidence)
    
    return PredictionResponse(
        predicted_grade=predicted_grade,
        confidence=round(confidence, 1),
        recommendations=recommendations
    )

def generate_recommendations(grade, confidence):
    if grade == 'A':
        return "Excellent! Keep up your great study habits. Consider helping peers who may need assistance."
    elif grade == 'B+':
        return "Very good performance. Focus on challenging topics to reach excellence."
    elif grade == 'B':
        return "Good performance. Review difficult concepts and maintain consistent study schedule."
    elif grade == 'C+':
        return "Satisfactory. Increase study time and seek help for challenging topics."
    elif grade == 'C':
        return "You may need additional support. Attend tutorials and consult with lecturers."
    elif grade == 'D+':
        return "Below average. Meet with your academic advisor to develop a study improvement plan."
    elif grade == 'D':
        return "Poor performance. Urgent action needed. Schedule meeting with your advisor immediately."
    else:
        return "Failing. Immediate intervention required. Contact your academic advisor today."

@app.get("/api/dashboard/stats", response_model=DashboardStats)
def dashboard_stats(token: str = Depends(oauth2_scheme), db: Session = Depends(lambda: SessionLocal())):
    # Verify user
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = get_user(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user's predictions
    predictions = db.query(Prediction).filter(Prediction.user_id == user.id).all()
    
    # Calculate stats (simplified for demo)
    gpa = 3.45  # In real app, calculate from actual grades
    credits_completed = 72
    credits_remaining = 48
    courses_enrolled = 5
    
    return DashboardStats(
        gpa=gpa,
        credits_completed=credits_completed,
        credits_remaining=credits_remaining,
        courses_enrolled=courses_enrolled
    )

@app.get("/api/predictions/history")
def prediction_history(token: str = Depends(oauth2_scheme), db: Session = Depends(lambda: SessionLocal())):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = get_user(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    predictions = db.query(Prediction).filter(Prediction.user_id == user.id).order_by(Prediction.created_at.desc()).all()
    
    return [
        {
            "id": p.id,
            "course_code": p.course_code,
            "predicted_grade": p.predicted_grade,
            "confidence": p.confidence_score,
            "actual_grade": p.actual_grade,
            "created_at": p.created_at
        }
        for p in predictions
    ]

@app.get("/api/predictions/recent")
def recent_predictions(token: str = Depends(oauth2_scheme), db: Session = Depends(lambda: SessionLocal())):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = get_user(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    predictions = db.query(Prediction).filter(Prediction.user_id == user.id).order_by(Prediction.created_at.desc()).limit(5).all()
    
    return [
        {
            "id": p.id,
            "course_code": p.course_code,
            "predicted_grade": p.predicted_grade,
            "confidence": p.confidence_score,
            "created_at": p.created_at
        }
        for p in predictions
    ]

@app.get("/api/profile")
def get_profile(token: str = Depends(oauth2_scheme), db: Session = Depends(lambda: SessionLocal())):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = get_user(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    predictions_count = db.query(Prediction).filter(Prediction.user_id == user.id).count()
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "student_id": user.student_id,
        "created_at": user.created_at,
        "predictions_count": predictions_count
    }

@app.put("/api/profile/update")
def update_profile(request: dict, token: str = Depends(oauth2_scheme), db: Session = Depends(lambda: SessionLocal())):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = get_user(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if "full_name" in request:
        user.full_name = request["full_name"]
    
    db.commit()
    return {"success": True, "message": "Profile updated successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
