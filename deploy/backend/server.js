const express = require('express');
const mysql = require('mysql2/promise');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const cors = require('cors');
const dotenv = require('dotenv');
const morgan = require('morgan');
const helmet = require('helmet');

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;

app.use(helmet());
app.use(cors());
app.use(express.json());
app.use(morgan('dev'));

const db = mysql.createPool({
    host: process.env.DB_HOST || 'localhost',
    user: process.env.DB_USER || 'root',
    password: process.env.DB_PASSWORD || '',
    database: process.env.DB_NAME || 'aamusted_predictor',
    port: 3306,
    waitForConnections: true,
    connectionLimit: 10,
    queueLimit: 0
});

async function testDatabase() {
    try {
        const connection = await db.getConnection();
        console.log('✅ Database connected successfully!');
        connection.release();
        return true;
    } catch (error) {
        console.error('❌ Database connection failed:', error.message);
        return false;
    }
}

const JWT_SECRET = process.env.JWT_SECRET || 'aamusted_predictor_secret_key_2024';
const JWT_EXPIRES_IN = '7d';

const authenticateToken = async (req, res, next) => {
    const authHeader = req.headers.authorization;
    const token = authHeader && authHeader.split(' ')[1];

    if (!token) {
        return res.status(401).json({ success: false, error: 'Access token required' });
    }

    try {
        const decoded = jwt.verify(token, JWT_SECRET);
        req.user = decoded;
        next();
    } catch (error) {
        return res.status(403).json({ success: false, error: 'Invalid or expired token' });
    }
};

function getGradeDescription(grade) {
    const descriptions = {
        'A': 'Excellent! You are performing exceptionally well.',
        'B': 'Very Good! Keep up the great work.',
        'C': 'Good! You are on the right track.',
        'D': 'Satisfactory. You need to put in more effort.',
        'F': 'Needs Improvement. Please seek help from your lecturer.'
    };
    return descriptions[grade] || 'Performance predicted successfully.';
}

function getRecommendation(grade) {
    const recommendations = {
        'A': 'Maintain your excellent performance. Help classmates who may be struggling.',
        'B': 'Keep up the good work! Focus on challenging topics.',
        'C': 'Increase study time by 2-3 hours per week.',
        'D': 'Attend all classes and seek help from your lecturer.',
        'F': 'Meet with your lecturer and academic advisor immediately.'
    };
    return recommendations[grade] || 'Stay focused and keep working hard.';
}

// ================ LOGIN ENDPOINT ================

app.post('/api/login', async (req, res) => {
    try {
        const { username, password } = req.body;
        
        console.log('🔐 Login attempt for:', username);

        const query = "SELECT u.*, s.index_number, s.level, s.program_type, l.staff_id FROM users u LEFT JOIN students s ON u.id = s.user_id LEFT JOIN lecturers l ON u.id = l.user_id WHERE u.username = ? OR u.email = ?";
        const [users] = await db.query(query, [username, username]);

        if (users.length === 0) {
            console.log('❌ User not found:', username);
            return res.status(401).json({ success: false, error: 'Invalid credentials' });
        }

        const user = users[0];
        console.log('✅ User found:', user.username);
        console.log('📝 Stored password:', user.password);
        console.log('🔑 Provided password:', password);
        
        const validPassword = (password === user.password);
        
        console.log('✓ Password valid:', validPassword);
        
        if (!validPassword) {
            return res.status(401).json({ success: false, error: 'Invalid credentials' });
        }

        const token = jwt.sign(
            { id: user.id, username: user.username, role: user.role, full_name: user.full_name }, 
            JWT_SECRET, 
            { expiresIn: JWT_EXPIRES_IN }
        );

        const userData = { 
            id: user.id, 
            full_name: user.full_name, 
            username: user.username, 
            email: user.email, 
            role: user.role, 
            department: user.department 
        };
        
        if (user.role === 'student') {
            userData.index_number = user.index_number;
            userData.level = user.level;
            userData.program_type = user.program_type;
        } else if (user.role === 'lecturer') {
            userData.staff_id = user.staff_id;
        }

        console.log('🎉 Login successful for:', user.username);
        res.json({ success: true, token, user: userData });
        
    } catch (error) {
        console.error('❌ Login error:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

// ================ REGISTER ENDPOINT ================

app.post('/api/register', async (req, res) => {
    try {
        const { full_name, username, email, password, role, department, index_number, level, program_type, staff_id } = req.body;

        const [existing] = await db.query('SELECT id FROM users WHERE username = ? OR email = ?', [username, email]);
        if (existing.length > 0) {
            return res.status(400).json({ success: false, error: 'Username or email already exists' });
        }

        const hashedPassword = await bcrypt.hash(password, 10);
        const [userResult] = await db.query(
            'INSERT INTO users (full_name, username, email, password, role, department) VALUES (?, ?, ?, ?, ?, ?)',
            [full_name, username, email, hashedPassword, role, department]
        );

        const userId = userResult.insertId;

        if (role === 'student') {
            await db.query('INSERT INTO students (user_id, index_number, level, program_type) VALUES (?, ?, ?, ?)',
                [userId, index_number, level || '100', program_type || 'regular']);
        } else if (role === 'lecturer') {
            await db.query('INSERT INTO lecturers (user_id, staff_id) VALUES (?, ?)', [userId, staff_id]);
        }

        const token = jwt.sign({ id: userId, username, role, full_name }, JWT_SECRET, { expiresIn: JWT_EXPIRES_IN });

        res.json({ success: true, token, user: { id: userId, full_name, username, email, role, department } });
    } catch (error) {
        console.error('Registration error:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

// ================ PROFILE ENDPOINT ================

app.get('/api/profile', authenticateToken, async (req, res) => {
    try {
        const query = "SELECT u.*, s.index_number, s.level, s.program_type, l.staff_id FROM users u LEFT JOIN students s ON u.id = s.user_id LEFT JOIN lecturers l ON u.id = l.user_id WHERE u.id = ?";
        const [users] = await db.query(query, [req.user.id]);

        if (users.length === 0) {
            return res.status(404).json({ success: false, error: 'User not found' });
        }

        const user = users[0];
        const userData = { id: user.id, full_name: user.full_name, username: user.username, email: user.email, role: user.role, department: user.department };
        
        if (user.role === 'student') {
            userData.index_number = user.index_number;
            userData.level = user.level;
            userData.program_type = user.program_type;
        } else if (user.role === 'lecturer') {
            userData.staff_id = user.staff_id;
        }

        res.json({ success: true, user: userData });
    } catch (error) {
        console.error('Profile error:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

// ================ UPDATE PROFILE ENDPOINT ================

app.put('/api/profile', authenticateToken, async (req, res) => {
    try {
        const { full_name, email, department, index_number, level, program_type, staff_id } = req.body;
        const userId = req.user.id;

        await db.query('UPDATE users SET full_name = ?, email = ?, department = ? WHERE id = ?', [full_name, email, department, userId]);

        const [user] = await db.query('SELECT role FROM users WHERE id = ?', [userId]);
        
        if (user[0].role === 'student') {
            await db.query('UPDATE students SET index_number = ?, level = ?, program_type = ? WHERE user_id = ?', [index_number, level, program_type, userId]);
        } else if (user[0].role === 'lecturer') {
            await db.query('UPDATE lecturers SET staff_id = ? WHERE user_id = ?', [staff_id, userId]);
        }

        res.json({ success: true, message: 'Profile updated successfully' });
    } catch (error) {
        console.error('Profile update error:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

// ================ STUDENT COURSES ENDPOINTS ================

app.get('/api/student/:studentId/courses', authenticateToken, async (req, res) => {
    try {
        const [student] = await db.query('SELECT id FROM students WHERE user_id = ?', [req.params.studentId]);
        if (student.length === 0) {
            return res.json({ success: true, courses: [], count: 0 });
        }

        const query = "SELECT c.*, sc.enrolled_date FROM courses c JOIN student_courses sc ON c.id = sc.course_id WHERE sc.student_id = ? ORDER BY c.course_code";
        const [courses] = await db.query(query, [student[0].id]);

        res.json({ success: true, courses, count: courses.length });
    } catch (error) {
        console.error('Error fetching courses:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

app.post('/api/student/:studentId/courses', authenticateToken, async (req, res) => {
    try {
        const { course_code, course_name, credits } = req.body;
        const [student] = await db.query('SELECT id FROM students WHERE user_id = ?', [req.params.studentId]);
        
        if (student.length === 0) {
            return res.status(404).json({ success: false, error: 'Student not found' });
        }

        let [course] = await db.query('SELECT id FROM courses WHERE course_code = ?', [course_code]);
        let courseId;
        
        if (course.length === 0) {
            const [result] = await db.query('INSERT INTO courses (course_code, course_name, credits) VALUES (?, ?, ?)', [course_code, course_name, credits]);
            courseId = result.insertId;
        } else {
            courseId = course[0].id;
        }

        const [existing] = await db.query('SELECT * FROM student_courses WHERE student_id = ? AND course_id = ?', [student[0].id, courseId]);
        if (existing.length > 0) {
            return res.status(400).json({ success: false, error: 'Already enrolled' });
        }

        await db.query('INSERT INTO student_courses (student_id, course_id) VALUES (?, ?)', [student[0].id, courseId]);
        res.json({ success: true, message: 'Course added successfully', course: { id: courseId, course_code, course_name, credits } });
    } catch (error) {
        console.error('Error adding course:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

app.delete('/api/student/:studentId/courses/:courseId', authenticateToken, async (req, res) => {
    try {
        const [student] = await db.query('SELECT id FROM students WHERE user_id = ?', [req.params.studentId]);
        if (student.length === 0) {
            return res.status(404).json({ success: false, error: 'Student not found' });
        }

        await db.query('DELETE FROM student_courses WHERE student_id = ? AND course_id = ?', [student[0].id, req.params.courseId]);
        res.json({ success: true, message: 'Course removed successfully' });
    } catch (error) {
        console.error('Error removing course:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

// ================ PREDICTIONS ENDPOINTS ================

app.post('/api/predict', authenticateToken, async (req, res) => {
    try {
        const { student_id, course_code, course_name, credits } = req.body;

        const [previous] = await db.query('SELECT predicted_score, actual_score FROM predictions WHERE student_id = ? ORDER BY created_at DESC LIMIT 5', [student_id]);

        let avgScore = 70;
        if (previous.length > 0) {
            let sum = 0;
            for (let p of previous) {
                sum += p.actual_score || p.predicted_score;
            }
            avgScore = sum / previous.length;
        }

        const variation = Math.floor(Math.random() * 15) - 7;
        let predictedScore = Math.min(100, Math.max(40, Math.round(avgScore + variation)));
        
        let grade;
        if (predictedScore >= 80) grade = 'A';
        else if (predictedScore >= 70) grade = 'B';
        else if (predictedScore >= 60) grade = 'C';
        else if (predictedScore >= 50) grade = 'D';
        else grade = 'F';

        const [result] = await db.query(
            'INSERT INTO predictions (student_id, course_code, course_name, credits, predicted_score, predicted_grade) VALUES (?, ?, ?, ?, ?, ?)',
            [student_id, course_code, course_name, credits, predictedScore, grade]
        );

        res.json({
            success: true,
            prediction: {
                id: result.insertId,
                score: predictedScore,
                grade: grade,
                description: getGradeDescription(grade),
                recommendation: getRecommendation(grade)
            }
        });
    } catch (error) {
        console.error('Prediction error:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

app.get('/api/student/:studentId/predictions', authenticateToken, async (req, res) => {
    try {
        const [predictions] = await db.query('SELECT * FROM predictions WHERE student_id = ? ORDER BY created_at DESC LIMIT 50', [req.params.studentId]);
        res.json({ success: true, predictions, count: predictions.length });
    } catch (error) {
        console.error('Error fetching predictions:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

app.post('/api/logout', authenticateToken, async (req, res) => {
    res.json({ success: true, message: 'Logged out successfully' });
});

// ================ START SERVER ================

app.listen(PORT, async () => {
    console.log('🚀 Server running on port ' + PORT);
    console.log('📍 API URL: http://localhost:' + PORT);
    await testDatabase();
});

process.on('SIGINT', async () => {
    console.log('\n👋 Shutting down server...');
    await db.end();
    process.exit(0);
});
