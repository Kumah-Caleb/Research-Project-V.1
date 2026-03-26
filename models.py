# models.py - Database Models
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='student')
    full_name = db.Column(db.String(100), nullable=False)
    index_number = db.Column(db.String(10), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    predictions = db.relationship('Prediction', backref='user', lazy=True, cascade="all, delete-orphan")
    courses = db.relationship('UserCourse', backref='user', lazy=True, cascade="all, delete-orphan")
    taught_courses = db.relationship('Course', backref='lecturer', lazy=True)

class Course(db.Model):
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=False)
    credit_hours = db.Column(db.Integer, default=3)
    lecturer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user_courses = db.relationship('UserCourse', backref='course', lazy=True)

class UserCourse(db.Model):
    __tablename__ = 'user_courses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    
    attendance = db.Column(db.Float, default=0)
    assignments = db.Column(db.Float, default=0)
    engagement = db.Column(db.Float, default=0)
    study_hours = db.Column(db.Float, default=0)
    previous_grade = db.Column(db.Float, default=0)
    extra_curricular = db.Column(db.Integer, default=2)
    parent_education = db.Column(db.Integer, default=2)
    
    predicted_grade = db.Column(db.String(5))
    weighted_score = db.Column(db.Float)
    
    strengths = db.Column(db.Text)
    weaknesses = db.Column(db.Text)
    recommendations = db.Column(db.Text)
    
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Prediction(db.Model):
    __tablename__ = 'predictions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True)
    
    attendance = db.Column(db.Float)
    assignments = db.Column(db.Float)
    engagement = db.Column(db.Float)
    study_hours = db.Column(db.Float)
    previous_grade = db.Column(db.Float)
    extra_curricular = db.Column(db.Integer)
    parent_education = db.Column(db.Integer)
    
    predicted_grade = db.Column(db.String(5))
    weighted_score = db.Column(db.Float)
    confidence = db.Column(db.Float)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)