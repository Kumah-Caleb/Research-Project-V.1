const express = require('express');
const { Pool } = require('pg');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const cors = require('cors');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

// Log environment variables (don't log password in production)
console.log('DATABASE_URL exists:', !!process.env.DATABASE_URL);
console.log('DB_HOST:', process.env.DB_HOST);
console.log('DB_NAME:', process.env.DB_NAME);
console.log('DB_USER:', process.env.DB_USER);

// PostgreSQL connection
let pool;
try {
    // Use DATABASE_URL if available
    if (process.env.DATABASE_URL) {
        pool = new Pool({
            connectionString: process.env.DATABASE_URL,
            ssl: { rejectUnauthorized: false }
        });
        console.log('Using DATABASE_URL for connection');
    } else {
        // Use individual parameters
        pool = new Pool({
            host: process.env.DB_HOST || 'dpg-d726egvdiees739hojv0-a.oregon-postgres.render.com',
            port: process.env.DB_PORT || 5432,
            database: process.env.DB_NAME || 'student_performance_db_1f4u',
            user: process.env.DB_USER || 'student_performance_db_1f4u_user',
            password: process.env.DB_PASSWORD,
            ssl: { rejectUnauthorized: false }
        });
        console.log('Using individual DB parameters');
    }
    
    // Test connection
    pool.connect((err, client, release) => {
        if (err) {
            console.error('❌ Database connection error:', err.message);
            console.error('Error details:', err);
        } else {
            console.log('✅ Connected to PostgreSQL database!');
            release();
        }
    });
} catch (error) {
    console.error('❌ Failed to create database pool:', error.message);
}

app.get('/', (req, res) => {
    res.json({ 
        status: 'ok', 
        message: 'AAMUSTED Performance Predictor API',
        endpoints: {
            login: 'POST /api/login',
            profile: 'GET /api/profile',
            courses: 'GET /api/student/:studentId/courses',
            predict: 'POST /api/predict'
        }
    });
});

app.post('/api/login', async (req, res) => {
    try {
        const { username, password } = req.body;
        
        if (!pool) {
            return res.status(500).json({ success: false, error: 'Database not connected' });
        }
        
        const result = await pool.query(
            'SELECT * FROM users WHERE username = ',
            [username]
        );
        
        if (result.rows.length === 0) {
            return res.status(401).json({ success: false, error: 'Invalid credentials' });
        }
        
        const user = result.rows[0];
        
        if (password !== user.password) {
            return res.status(401).json({ success: false, error: 'Invalid credentials' });
        }
        
        const token = jwt.sign(
            { id: user.id, username: user.username, role: user.role },
            process.env.JWT_SECRET || 'secret',
            { expiresIn: '7d' }
        );
        
        res.json({
            success: true,
            token,
            user: {
                id: user.id,
                full_name: user.full_name,
                username: user.username,
                email: user.email,
                role: user.role,
                department: user.department
            }
        });
    } catch (error) {
        console.error('Login error:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

app.get('/api/student/:studentId/courses', async (req, res) => {
    try {
        if (!pool) {
            return res.status(500).json({ success: false, error: 'Database not connected' });
        }
        
        const result = await pool.query(
            SELECT c.*, sc.enrolled_date 
            FROM courses c
            JOIN student_courses sc ON c.id = sc.course_id
            JOIN students s ON sc.student_id = s.id
            WHERE s.user_id = 
        , [req.params.studentId]);
        
        res.json({ success: true, courses: result.rows, count: result.rows.length });
    } catch (error) {
        console.error('Courses error:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

app.post('/api/predict', async (req, res) => {
    try {
        const { student_id, course_code, course_name, credits } = req.body;
        
        if (!pool) {
            return res.status(500).json({ success: false, error: 'Database not connected' });
        }
        
        const predictedScore = Math.floor(Math.random() * (85 - 55 + 1) + 55);
        let grade = 'C';
        if (predictedScore >= 80) grade = 'A';
        else if (predictedScore >= 70) grade = 'B';
        else if (predictedScore >= 60) grade = 'C';
        else if (predictedScore >= 50) grade = 'D';
        else grade = 'F';
        
        const result = await pool.query(
            'INSERT INTO predictions (student_id, course_code, course_name, credits, predicted_score, predicted_grade) VALUES (, , , , , ) RETURNING id',
            [student_id, course_code, course_name, credits, predictedScore, grade]
        );
        
        res.json({
            success: true,
            prediction: {
                id: result.rows[0].id,
                score: predictedScore,
                grade: grade,
                description: 'Prediction generated successfully',
                recommendation: 'Keep studying!'
            }
        });
    } catch (error) {
        console.error('Prediction error:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

app.listen(PORT, () => {
    console.log(🚀 Server running on port );
    console.log(📍 API URL: http://localhost:);
});
