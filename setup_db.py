import psycopg2

try:
    print("Connecting to Render PostgreSQL...")
    conn = psycopg2.connect("postgresql://student_performance_db_1f4u_user:DvLfjBlmxuwdQlyLPd7ZAfnBquaHgriJ@dpg-d726egvdiees739hojv0-a.oregon-postgres.render.com/student_performance_db_1f4u")
    print("✅ Connected successfully!")
    
    cur = conn.cursor()
    
    # Create users table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        full_name VARCHAR(255) NOT NULL,
        username VARCHAR(100) UNIQUE NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        role VARCHAR(20) CHECK (role IN ('student', 'lecturer')) NOT NULL,
        department VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    print("✅ users table created")
    
    # Create students table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        index_number VARCHAR(50) UNIQUE NOT NULL,
        level VARCHAR(20) DEFAULT '100',
        program_type VARCHAR(20) DEFAULT 'regular',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    print("✅ students table created")
    
    # Create courses table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        id SERIAL PRIMARY KEY,
        course_code VARCHAR(20) UNIQUE NOT NULL,
        course_name VARCHAR(255) NOT NULL,
        credits INTEGER DEFAULT 3,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    print("✅ courses table created")
    
    # Create student_courses table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS student_courses (
        id SERIAL PRIMARY KEY,
        student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
        course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
        enrolled_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(student_id, course_id)
    )
    """)
    print("✅ student_courses table created")
    
    # Insert sample user
    cur.execute("""
    INSERT INTO users (full_name, username, email, password, role, department) 
    VALUES ('Amoateng Gideon', 'amoateng', 'amoateng@aamusted.edu.gh', 'student123', 'student', 'Information Technology')
    ON CONFLICT (username) DO NOTHING
    """)
    print("✅ Sample user inserted")
    
    # Insert student record
    cur.execute("""
    INSERT INTO students (user_id, index_number, level, program_type)
    SELECT id, '5230100757', '200', 'regular'
    FROM users WHERE username = 'amoateng'
    ON CONFLICT (index_number) DO NOTHING
    """)
    print("✅ Student record inserted")
    
    # Insert courses
    cur.execute("""
    INSERT INTO courses (course_code, course_name, credits) VALUES
    ('CSC 101', 'Introduction to Computer Science', 3),
    ('MATH 101', 'Algebra and Trigonometry', 3),
    ('STAT 101', 'Introduction to Statistics', 3)
    ON CONFLICT (course_code) DO NOTHING
    """)
    print("✅ Courses inserted")
    
    # Enroll student
    cur.execute("""
    INSERT INTO student_courses (student_id, course_id)
    SELECT s.id, c.id 
    FROM students s, courses c 
    WHERE s.user_id = (SELECT id FROM users WHERE username = 'amoateng')
    AND c.course_code IN ('CSC 101', 'MATH 101', 'STAT 101')
    ON CONFLICT (student_id, course_id) DO NOTHING
    """)
    print("✅ Student enrolled in courses")
    
    conn.commit()
    
    # Verify
    cur.execute("SELECT COUNT(*) FROM users")
    users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM courses")
    courses = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM student_courses")
    enrollments = cur.fetchone()[0]
    
    print(f"\n📊 Database Summary:")
    print(f"   Users: {users}")
    print(f"   Courses: {courses}")
    print(f"   Enrollments: {enrollments}")
    
    cur.close()
    conn.close()
    print("\n🎉 Database setup complete!")
    
except Exception as e:
    print(f"❌ Error: {e}")