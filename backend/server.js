const express = require('express');
const { Pool } = require('pg');
const jwt = require('jsonwebtoken');
const cors = require('cors');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

// Database connection
let pool;
try {
    const connectionString = process.env.DATABASE_URL || 'postgresql://student_performance_db_1f4u_user:DvLfjBlmxuwdQlyLPd7ZAfnBquaHgriJ@dpg-d726egvdiees739hojv0-a.oregon-postgres.render.com/student_performance_db_1f4u';
    pool = new Pool({
        connectionString: connectionString,
        ssl: { rejectUnauthorized: false }
    });
    console.log('Database configured');
    
    pool.connect((err, client, release) => {
        if (err) {
            console.log('Database connection error:', err.message);
        } else {
            console.log('Connected to PostgreSQL');
            release();
        }
    });
} catch (err) {
    console.log('Pool creation error:', err.message);
}

// Root endpoint
app.get('/', (req, res) => {
    res.json({ 
        status: 'ok',
        message: 'AAMUSTED Performance Predictor API',
        endpoints: ['/api/login', '/api/profile', '/api/student/:id/courses', '/api/predict']
    });
});

// Login endpoint
app.post('/api/login', async (req, res) => {
    try {
        const { username, password } = req.body;
        console.log('Login attempt for:', username);
        
        if (!pool) {
            return res.status(500).json({ success: false, error: 'Database not connected' });
        }
        
        const result = await pool.query('SELECT * FROM users WHERE username = ', [username]);
        
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
            token: token,
            user: {
                id: user.id,
                full_name: user.full_name,
                username: user.username,
                email: user.email,
                role: user.role,
                department: user.department
            }
        });
    } catch (err) {
        console.error('Login error:', err);
        res.status(500).json({ success: false, error: err.message });
    }
});

// Profile endpoint
app.get('/api/profile', async (req, res) => {
    const authHeader = req.headers.authorization;
    const token = authHeader && authHeader.split(' ')[1];
    
    if (!token) {
        return res.status(401).json({ success: false, error: 'No token provided' });
    }
    
    try {
        const decoded = jwt.verify(token, process.env.JWT_SECRET || 'secret');
        const result = await pool.query('SELECT * FROM users WHERE id = ', [decoded.id]);
        
        if (result.rows.length === 0) {
            return res.status(404).json({ success: false, error: 'User not found' });
        }
        
        const user = result.rows[0];
        res.json({
            success: true,
            user: {
                id: user.id,
                full_name: user.full_name,
                username: user.username,
                email: user.email,
                role: user.role,
                department: user.department
            }
        });
    } catch (err) {
        console.error('Profile error:', err);
        res.status(401).json({ success: false, error: 'Invalid token' });
    }
});

// Get student courses
app.get('/api/student/:studentId/courses', async (req, res) => {
    try {
        if (!pool) {
            return res.status(500).json({ success: false, error: 'Database not connected' });
        }
        
        const sql = 'SELECT c.*, sc.enrolled_date FROM courses c JOIN student_courses sc ON c.id = sc.course_id JOIN students s ON sc.student_id = s.id WHERE s.user_id = ';
        const result = await pool.query(sql, [req.params.studentId]);
        
        res.json({ success: true, courses: result.rows, count: result.rows.length });
    } catch (err) {
        console.error('Courses error:', err);
        res.status(500).json({ success: false, error: err.message });
    }
});

// Make prediction
app.post('/api/predict', async (req, res) => {
    try {
        const { student_id, course_code, course_name, credits } = req.body;
        
        if (!pool) {
            return res.status(500).json({ success: false, error: 'Database not connected' });
        }
        
        const score = Math.floor(Math.random() * (85 - 55 + 1) + 55);
        let grade = 'C';
        if (score >= 80) grade = 'A';
        else if (score >= 70) grade = 'B';
        else if (score >= 60) grade = 'C';
        else if (score >= 50) grade = 'D';
        else grade = 'F';
        
        const sql = 'INSERT INTO predictions (student_id, course_code, course_name, credits, predicted_score, predicted_grade) VALUES (, , , , , ) RETURNING id';
        const result = await pool.query(sql, [student_id, course_code, course_name, credits, score, grade]);
        
        res.json({
            success: true,
            prediction: {
                id: result.rows[0].id,
                score: score,
                grade: grade,
                description: 'Prediction generated',
                recommendation: 'Keep studying'
            }
        });
    } catch (err) {
        console.error('Prediction error:', err);
        res.status(500).json({ success: false, error: err.message });
    }
});

// Start server
app.listen(PORT, () => {
    console.log('Server running on port ' + PORT);
    console.log('API URL: http://localhost:' + PORT);
});
