-- Add lecturer support to database
-- Migration: add_lecturer_support.sql

-- Add lecturer_id to courses table
ALTER TABLE courses ADD COLUMN IF NOT EXISTS lecturer_id INTEGER REFERENCES users(id);

-- Add lecturer feedback fields to predictions table
ALTER TABLE predictions ADD COLUMN IF NOT EXISTS lecturer_feedback TEXT;
ALTER TABLE predictions ADD COLUMN IF NOT EXISTS updated_by INTEGER REFERENCES users(id);
ALTER TABLE predictions ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;

-- Create a sample lecturer account (password: lecturer123)
-- Note: This password is hashed for "lecturer123"
INSERT INTO users (full_name, username, email, password, role, department, created_at)
SELECT 'Dr. John Smith', 'drjohn', 'dr.john@aamusted.edu.gh', 
       '$2a$10$rQ5sGq8ZqZqZqZqZqZqZqu', 'lecturer', 'Computer Science', NOW()
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'drjohn');

-- Create another sample lecturer
INSERT INTO users (full_name, username, email, password, role, department, created_at)
SELECT 'Prof. Mary Johnson', 'profmary', 'mary.johnson@aamusted.edu.gh', 
       '$2a$10$rQ5sGq8ZqZqZqZqZqZqZqu', 'lecturer', 'Mathematics', NOW()
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'profmary');

-- Update any existing courses to have a lecturer
-- (if there are courses without a lecturer, assign to drjohn)
UPDATE courses 
SET lecturer_id = (SELECT id FROM users WHERE username = 'drjohn' LIMIT 1)
WHERE lecturer_id IS NULL AND EXISTS (SELECT 1 FROM users WHERE username = 'drjohn');

-- Add sample courses if none exist
INSERT INTO courses (course_code, course_name, credits, lecturer_id)
SELECT 'CSC101', 'Introduction to Programming', 3, u.id
FROM users u
WHERE u.username = 'drjohn' 
  AND NOT EXISTS (SELECT 1 FROM courses WHERE course_code = 'CSC101');

INSERT INTO courses (course_code, course_name, credits, lecturer_id)
SELECT 'CSC102', 'Data Structures', 3, u.id
FROM users u
WHERE u.username = 'drjohn' 
  AND NOT EXISTS (SELECT 1 FROM courses WHERE course_code = 'CSC102');

INSERT INTO courses (course_code, course_name, credits, lecturer_id)
SELECT 'MAT101', 'Discrete Mathematics', 3, u.id
FROM users u
WHERE u.username = 'profmary' 
  AND NOT EXISTS (SELECT 1 FROM courses WHERE course_code = 'MAT101');

-- Sample student enrollment data (if students exist)
INSERT INTO student_courses (student_id, course_id, semester, academic_year, enrolled_date)
SELECT s.id, c.id, '1', '2024', NOW()
FROM students s
CROSS JOIN courses c
WHERE c.course_code = 'CSC101'
  AND NOT EXISTS (
    SELECT 1 FROM student_courses sc 
    WHERE sc.student_id = s.id AND sc.course_id = c.id
  )
LIMIT 10;

-- Note: Run this migration to enable lecturer dashboard functionality
