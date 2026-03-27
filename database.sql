-- Create database
CREATE DATABASE IF NOT EXISTS aamusted_predictor;
USE aamusted_predictor;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    full_name VARCHAR(255) NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('student', 'lecturer') NOT NULL,
    department VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Students table
CREATE TABLE IF NOT EXISTS students (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    index_number VARCHAR(50) UNIQUE NOT NULL,
    level VARCHAR(20) DEFAULT '100',
    program_type ENUM('regular', 'non-regular') DEFAULT 'regular',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Lecturers table
CREATE TABLE IF NOT EXISTS lecturers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    staff_id VARCHAR(50) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Courses table
CREATE TABLE IF NOT EXISTS courses (
    id INT PRIMARY KEY AUTO_INCREMENT,
    course_code VARCHAR(20) UNIQUE NOT NULL,
    course_name VARCHAR(255) NOT NULL,
    credits INT DEFAULT 3,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Student Courses (Enrollment)
CREATE TABLE IF NOT EXISTS student_courses (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    enrolled_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    UNIQUE KEY unique_enrollment (student_id, course_id)
);

-- Lecturer Courses (Teaching Assignments)
CREATE TABLE IF NOT EXISTS lecturer_courses (
    id INT PRIMARY KEY AUTO_INCREMENT,
    lecturer_id INT NOT NULL,
    course_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lecturer_id) REFERENCES lecturers(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    UNIQUE KEY unique_assignment (lecturer_id, course_id)
);

-- Predictions table
CREATE TABLE IF NOT EXISTS predictions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    course_code VARCHAR(20) NOT NULL,
    course_name VARCHAR(255) NOT NULL,
    credits INT DEFAULT 3,
    predicted_score INT,
    predicted_grade VARCHAR(2),
    actual_score INT,
    actual_grade VARCHAR(2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

-- Insert sample student (password: student123)
-- The password hash is for 'student123' - you'll need to generate properly
INSERT INTO users (full_name, username, email, password, role, department) VALUES
('Amoateng Gideon', 'amoateng', 'amoateng@aamusted.edu.gh', '$2a$10$YourHashedPasswordHere', 'student', 'Information Technology');

-- Insert sample lecturer (password: lecturer123)
INSERT INTO users (full_name, username, email, password, role, department) VALUES
('Professor Asare', 'prof_asare', 'asare@aamusted.edu.gh', '$2a$10$YourHashedPasswordHere', 'lecturer', 'Information Technology');

-- Insert sample courses
INSERT INTO courses (course_code, course_name, credits) VALUES
('CSC 101', 'Introduction to Computer Science', 3),
('MATH 101', 'Algebra and Trigonometry', 3),
('STAT 101', 'Introduction to Statistics', 3),
('CSC 201', 'Data Structures and Algorithms', 3),
('CSC 301', 'Database Management Systems', 3);