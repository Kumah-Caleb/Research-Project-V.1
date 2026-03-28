const express = require('express');
const { Pool } = require('pg');
const jwt = require('jsonwebtoken');
const cors = require('cors');
const bcrypt = require('bcryptjs');
require('dotenv').config();

const app = express();
const DEFAULT_PORT = process.env.PORT || 3000;

// Middleware
app.use(cors({
    origin: ['http://localhost:3000', 'http://localhost:5173', 'https://aamusted-predictor-frontend.onrender.com'],
    credentials: true
}));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Database connection
let pool;
try {
    const connectionString = process.env.DATABASE_URL;
    if (!connectionString) {
        console.error('❌ DATABASE_URL not found in environment variables');
        process.exit(1);
    }
    
    pool = new Pool({
        connectionString: connectionString,
        ssl: { rejectUnauthorized: false },
        max: 20,
        idleTimeoutMillis: 30000,
        connectionTimeoutMillis: 2000,
    });
    console.log('✅ Database configured');
    
    pool.connect((err, client, release) => {
        if (err) {
            console.error('❌ Database connection error:', err.message);
        } else {
            console.log('✅ Connected to PostgreSQL');
            release();
        }
    });
} catch (err) {
    console.error('❌ Pool creation error:', err.message);
    process.exit(1);
}

// Authentication middleware
const authenticateToken = (req, res, next) => {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];
    
    if (!token) {
        return res.status(401).json({ success: false, error: 'Access token required' });
    }
    
    jwt.verify(token, process.env.JWT_SECRET || 'secret', (err, user) => {
        if (err) {
            return res.status(403).json({ success: false, error: 'Invalid or expired token' });
        }
        req.user = user;
        next();
    });
};

// Root endpoint
app.get('/', (req, res) => {
    res.json({ 
        status: 'ok',
        message: 'AAMUSTED Performance Predictor API',
        version: '1.0.0',
        timestamp: new Date().toISOString(),
        endpoints: {
            root: '/',
            login: '/api/login',
            register: '/api/register',
            profile: '/api/profile',
            courses: '/api/student/:studentId/courses',
            predict: '/api/predict',
            predictions: '/api/student/:studentId/predictions',
            health: '/api/health'
        }
    });
});

// Health check endpoint
app.get('/api/health', async (req, res) => {
    let dbStatus = 'disconnected';
    try {
        await pool.query('SELECT NOW()');
        dbStatus = 'connected';
    } catch (err) {
        dbStatus = 'error';
    }
    
    res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        database: dbStatus,
        uptime: process.uptime(),
        memory: process.memoryUsage(),
        environment: process.env.NODE_ENV
    });
});

// Register endpoint
app.post('/api/register', async (req, res) => {
    try {
        const { full_name, username, email, password, role = 'student', department } = req.body;
        
        // Validation
        if (!full_name || !username || !email || !password) {
            return res.status(400).json({ success: false, error: 'All fields are required' });
        }
        
        if (password.length < 6) {
            return res.status(400).json({ success: false, error: 'Password must be at least 6 characters' });
        }
        
        // Check if user exists
        const existingUser = await pool.query(
            'SELECT * FROM users WHERE username = $1 OR email = $2',
            [username, email]
        );
        
        if (existingUser.rows.length > 0) {
            return res.status(409).json({ success: false, error: 'Username or email already exists' });
        }
        
        // Hash password
        const hashedPassword = await bcrypt.hash(password, 10);
        
        // Create user
        const result = await pool.query(
            `INSERT INTO users (full_name, username, email, password, role, department, created_at) 
             VALUES ($1, $2, $3, $4, $5, $6, NOW()) RETURNING id, full_name, username, email, role, department`,
            [full_name, username, email, hashedPassword, role, department]
        );
        
        const user = result.rows[0];
        
        // Create token
        const token = jwt.sign(
            { id: user.id, username: user.username, role: user.role },
            process.env.JWT_SECRET || 'secret',
            { expiresIn: '7d' }
        );
        
        res.status(201).json({
            success: true,
            token: token,
            user: user
        });
    } catch (err) {
        console.error('Registration error:', err);
        res.status(500).json({ success: false, error: err.message });
    }
});

// Login endpoint
app.post('/api/login', async (req, res) => {
    try {
        const { username, password } = req.body;
        console.log('Login attempt for:', username);
        
        if (!username || !password) {
            return res.status(400).json({ success: false, error: 'Username and password required' });
        }
        
        if (!pool) {
            return res.status(500).json({ success: false, error: 'Database not connected' });
        }
        
        const result = await pool.query(
            'SELECT * FROM users WHERE username = $1 OR email = $1',
            [username]
        );
        
        if (result.rows.length === 0) {
            return res.status(401).json({ success: false, error: 'Invalid credentials' });
        }
        
        const user = result.rows[0];
        
        // Compare password
        const validPassword = await bcrypt.compare(password, user.password);
        if (!validPassword) {
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
app.get('/api/profile', authenticateToken, async (req, res) => {
    try {
        const result = await pool.query(
            'SELECT id, full_name, username, email, role, department, created_at FROM users WHERE id = $1',
            [req.user.id]
        );
        
        if (result.rows.length === 0) {
            return res.status(404).json({ success: false, error: 'User not found' });
        }
        
        res.json({
            success: true,
            user: result.rows[0]
        });
    } catch (err) {
        console.error('Profile error:', err);
        res.status(500).json({ success: false, error: err.message });
    }
});

// Get student courses
app.get('/api/student/:studentId/courses', authenticateToken, async (req, res) => {
    try {
        if (!pool) {
            return res.status(500).json({ success: false, error: 'Database not connected' });
        }
        
        const sql = `
            SELECT c.*, sc.enrolled_date, sc.semester, sc.academic_year 
            FROM courses c 
            JOIN student_courses sc ON c.id = sc.course_id 
            JOIN students s ON sc.student_id = s.id 
            WHERE s.user_id = $1
            ORDER BY sc.semester, c.course_code
        `;
        const result = await pool.query(sql, [req.params.studentId]);
        
        res.json({ 
            success: true, 
            courses: result.rows, 
            count: result.rows.length 
        });
    } catch (err) {
        console.error('Courses error:', err);
        res.status(500).json({ success: false, error: err.message });
    }
});

// Make prediction
app.post('/api/predict', authenticateToken, async (req, res) => {
    try {
        const { student_id, course_code, course_name, credits, semester, academic_year } = req.body;
        
        if (!student_id || !course_code || !course_name) {
            return res.status(400).json({ success: false, error: 'Missing required fields' });
        }
        
        if (!pool) {
            return res.status(500).json({ success: false, error: 'Database not connected' });
        }
        
        // Enhanced prediction algorithm based on student history
        let predictedScore, grade, recommendation;
        
        // Get student's previous performance
        const previousResults = await pool.query(
            `SELECT predicted_score FROM predictions 
             WHERE student_id = $1 
             ORDER BY created_at DESC 
             LIMIT 5`,
            [student_id]
        );
        
        const avgScore = previousResults.rows.length > 0
            ? previousResults.rows.reduce((sum, row) => sum + row.predicted_score, 0) / previousResults.rows.length
            : 70;
        
        // Generate prediction with some variability
        const baseScore = Math.min(95, Math.max(45, avgScore + (Math.random() * 10 - 5)));
        predictedScore = Math.floor(baseScore);
        
        // Determine grade
        if (predictedScore >= 80) grade = 'A';
        else if (predictedScore >= 70) grade = 'B';
        else if (predictedScore >= 60) grade = 'C';
        else if (predictedScore >= 50) grade = 'D';
        else grade = 'F';
        
        // Generate recommendation
        if (predictedScore >= 80) {
            recommendation = 'Excellent! Keep up the good work and maintain your study habits.';
        } else if (predictedScore >= 70) {
            recommendation = 'Good performance. Focus on challenging topics to improve further.';
        } else if (predictedScore >= 60) {
            recommendation = 'Satisfactory. Consider more practice and seek help for difficult concepts.';
        } else if (predictedScore >= 50) {
            recommendation = 'Needs improvement. Create a study schedule and consult with instructors.';
        } else {
            recommendation = 'Critical. Immediate intervention needed. Meet with academic advisor.';
        }
        
        const sql = `INSERT INTO predictions 
                     (student_id, course_code, course_name, credits, predicted_score, predicted_grade, recommendation, semester, academic_year, created_at) 
                     VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW()) 
                     RETURNING id`;
        const result = await pool.query(sql, [
            student_id, course_code, course_name, credits || 3, 
            predictedScore, grade, recommendation, semester, academic_year
        ]);
        
        res.json({
            success: true,
            prediction: {
                id: result.rows[0].id,
                score: predictedScore,
                grade: grade,
                recommendation: recommendation,
                confidence: Math.floor(Math.random() * (95 - 70 + 1) + 70),
                created_at: new Date().toISOString()
            }
        });
    } catch (err) {
        console.error('Prediction error:', err);
        res.status(500).json({ success: false, error: err.message });
    }
});

// Get student's prediction history
app.get('/api/student/:studentId/predictions', authenticateToken, async (req, res) => {
    try {
        const result = await pool.query(
            `SELECT * FROM predictions 
             WHERE student_id = $1 
             ORDER BY created_at DESC 
             LIMIT 50`,
            [req.params.studentId]
        );
        
        res.json({
            success: true,
            predictions: result.rows,
            count: result.rows.length
        });
    } catch (err) {
        console.error('Prediction history error:', err);
        res.status(500).json({ success: false, error: err.message });
    }
});

// Dashboard statistics
app.get('/api/dashboard/stats', authenticateToken, async (req, res) => {
    try {
        const stats = await pool.query(`
            SELECT 
                COUNT(DISTINCT course_code) as total_courses,
                AVG(predicted_score) as avg_score,
                COUNT(CASE WHEN predicted_grade IN ('A', 'B') THEN 1 END) as high_performance,
                COUNT(CASE WHEN predicted_grade = 'F' THEN 1 END) as at_risk
            FROM predictions 
            WHERE student_id = $1
        `, [req.user.id]);
        
        res.json({
            success: true,
            stats: stats.rows[0]
        });
    } catch (err) {
        console.error('Dashboard stats error:', err);
        res.status(500).json({ success: false, error: err.message });
    }
});

// Function to find available port
function findAvailablePort(startPort) {
    return new Promise((resolve, reject) => {
        const server = app.listen(startPort, () => {
            const { port } = server.address();
            server.close(() => resolve(port));
        });
        
        server.on('error', (err) => {
            if (err.code === 'EADDRINUSE') {
                resolve(findAvailablePort(startPort + 1));
            } else {
                reject(err);
            }
        });
    });
}

// Start server with automatic port selection
async function startServer() {
    try {
        const port = await findAvailablePort(DEFAULT_PORT);
        app.listen(port, () => {
            console.log(`✅ Server running on port ${port}`);
            console.log(`🌐 API URL: http://localhost:${port}`);
            console.log(`📝 Environment: ${process.env.NODE_ENV || 'development'}`);
        });
    } catch (err) {
        console.error('❌ Failed to start server:', err);
        process.exit(1);
    }
}

// Error handling middleware
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).json({ 
        success: false, 
        error: 'Internal server error',
        message: process.env.NODE_ENV === 'development' ? err.message : undefined
    });
});

// 404 handler
app.use((req, res) => {
    res.status(404).json({ 
        success: false, 
        error: 'Endpoint not found' 
    });
});

startServer();

// FIXED PREDICTION ENDPOINTS - Add these to your server.js

// Make prediction - Enhanced version
app.post('/api/predict', authenticateToken, async (req, res) => {
    try {
        const { student_id, course_code, course_name, credits, semester, academic_year } = req.body;
        
        if (!student_id || !course_code || !course_name) {
            return res.status(400).json({ success: false, error: 'Missing required fields' });
        }
        
        if (!pool) {
            return res.status(500).json({ success: false, error: 'Database not connected' });
        }
        
        // Get student's previous performance for better prediction
        const previousResults = await pool.query(
            `SELECT predicted_score FROM predictions 
             WHERE student_id = $1 
             ORDER BY created_at DESC 
             LIMIT 5`,
            [student_id]
        );
        
        const avgScore = previousResults.rows.length > 0
            ? previousResults.rows.reduce((sum, row) => sum + row.predicted_score, 0) / previousResults.rows.length
            : 70;
        
        // Generate prediction with some variability
        const baseScore = Math.min(95, Math.max(45, avgScore + (Math.random() * 10 - 5)));
        const predictedScore = Math.floor(baseScore);
        
        // Determine grade
        let grade;
        if (predictedScore >= 80) grade = 'A';
        else if (predictedScore >= 70) grade = 'B';
        else if (predictedScore >= 60) grade = 'C';
        else if (predictedScore >= 50) grade = 'D';
        else grade = 'F';
        
        // Generate recommendation
        let recommendation;
        if (predictedScore >= 80) {
            recommendation = 'Excellent! Keep up the good work and maintain your study habits.';
        } else if (predictedScore >= 70) {
            recommendation = 'Good performance. Focus on challenging topics to improve further.';
        } else if (predictedScore >= 60) {
            recommendation = 'Satisfactory. Consider more practice and seek help for difficult concepts.';
        } else if (predictedScore >= 50) {
            recommendation = 'Needs improvement. Create a study schedule and consult with instructors.';
        } else {
            recommendation = 'Critical. Immediate intervention needed. Meet with academic advisor.';
        }
        
        // Insert prediction with all fields
        const sql = `INSERT INTO predictions 
                     (student_id, course_code, course_name, credits, predicted_score, predicted_grade, recommendation, semester, academic_year, created_at) 
                     VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW()) 
                     RETURNING id, created_at`;
        
        const result = await pool.query(sql, [
            student_id, course_code, course_name, credits || 3, 
            predictedScore, grade, recommendation, semester || '1', academic_year || new Date().getFullYear().toString()
        ]);
        
        // Return the complete prediction
        res.json({
            success: true,
            prediction: {
                id: result.rows[0].id,
                course_code: course_code,
                course_name: course_name,
                credits: credits || 3,
                predicted_score: predictedScore,
                predicted_grade: grade,
                recommendation: recommendation,
                created_at: result.rows[0].created_at || new Date().toISOString()
            }
        });
        
    } catch (err) {
        console.error('Prediction error:', err);
        res.status(500).json({ success: false, error: err.message });
    }
});

// Get student's prediction history - Enhanced version
app.get('/api/student/:studentId/predictions', authenticateToken, async (req, res) => {
    try {
        const result = await pool.query(
            `SELECT id, student_id, course_code, course_name, credits, 
                    predicted_score, predicted_grade, recommendation, 
                    semester, academic_year, created_at
             FROM predictions 
             WHERE student_id = $1 
             ORDER BY created_at DESC 
             LIMIT 50`,
            [req.params.studentId]
        );
        
        console.log(`Found ${result.rows.length} predictions for student ${req.params.studentId}`);
        
        res.json({
            success: true,
            predictions: result.rows,
            count: result.rows.length
        });
    } catch (err) {
        console.error('Prediction history error:', err);
        res.status(500).json({ success: false, error: err.message });
    }
});

// Dashboard statistics - Enhanced version
app.get('/api/dashboard/stats', authenticateToken, async (req, res) => {
    try {
        const stats = await pool.query(`
            SELECT 
                COUNT(DISTINCT course_code) as total_courses,
                COALESCE(AVG(predicted_score), 0) as avg_score,
                COUNT(CASE WHEN predicted_grade IN ('A', 'B') THEN 1 END) as high_performance,
                COUNT(CASE WHEN predicted_grade = 'F' THEN 1 END) as at_risk
            FROM predictions 
            WHERE student_id = $1
        `, [req.user.id]);
        
        // Also get recent predictions for dashboard
        const recent = await pool.query(`
            SELECT course_code, course_name, predicted_score, predicted_grade, created_at
            FROM predictions 
            WHERE student_id = $1 
            ORDER BY created_at DESC 
            LIMIT 5
        `, [req.user.id]);
        
        console.log(`Dashboard stats: total=${stats.rows[0].total_courses}, recent=${recent.rows.length}`);
        
        res.json({
            success: true,
            stats: stats.rows[0],
            recent_predictions: recent.rows
        });
    } catch (err) {
        console.error('Dashboard stats error:', err);
        res.status(500).json({ success: false, error: err.message });
    }
});

// ============ LECTURER DASHBOARD ENDPOINTS ============

// Get lecturer dashboard data
app.get('/api/lecturer/dashboard', authenticateToken, async (req, res) => {
    try {
        console.log('Lecturer dashboard request from user:', req.user.id, 'role:', req.user.role);
        
        // Check if user is a lecturer
        if (req.user.role !== 'lecturer') {
            return res.status(403).json({ success: false, error: 'Access denied. Lecturer only.' });
        }
        
        // Get lecturer's courses with student counts
        const coursesResult = await pool.query(`
            SELECT 
                c.*,
                COUNT(DISTINCT sc.student_id) as enrolled_students,
                COALESCE(AVG(p.predicted_score), 0) as avg_performance
            FROM courses c
            LEFT JOIN student_courses sc ON c.id = sc.course_id
            LEFT JOIN predictions p ON p.course_code = c.course_code AND p.student_id = sc.student_id
            WHERE c.lecturer_id = $1 OR $1 IN (SELECT user_id FROM users WHERE role = 'admin')
            GROUP BY c.id
            ORDER BY c.course_code
        `, [req.user.id]);
        
        // Get overall statistics
        const statsResult = await pool.query(`
            SELECT 
                COUNT(DISTINCT c.id) as total_courses,
                COUNT(DISTINCT sc.student_id) as total_students,
                COALESCE(AVG(p.predicted_score), 0) as avg_performance,
                COUNT(DISTINCT CASE WHEN p.predicted_grade IN ('D', 'F') THEN sc.student_id END) as at_risk_students
            FROM courses c
            LEFT JOIN student_courses sc ON c.id = sc.course_id
            LEFT JOIN predictions p ON p.course_code = c.course_code AND p.student_id = sc.student_id
            WHERE c.lecturer_id = $1 OR $1 IN (SELECT user_id FROM users WHERE role = 'admin')
        `, [req.user.id]);
        
        // Get recent predictions for lecturer's courses
        const recentResult = await pool.query(`
            SELECT 
                p.*,
                u.full_name as student_name,
                u.email as student_email,
                c.course_name,
                c.course_code
            FROM predictions p
            JOIN students s ON p.student_id = s.id
            JOIN users u ON s.user_id = u.id
            JOIN courses c ON p.course_code = c.course_code
            WHERE c.lecturer_id = $1 OR $1 IN (SELECT user_id FROM users WHERE role = 'admin')
            ORDER BY p.created_at DESC
            LIMIT 10
        `, [req.user.id]);
        
        res.json({
            success: true,
            courses: coursesResult.rows,
            stats: statsResult.rows[0],
            recent_predictions: recentResult.rows
        });
        
    } catch (err) {
        console.error('Lecturer dashboard error:', err);
        res.status(500).json({ success: false, error: err.message });
    }
});

// Get students for a specific course
app.get('/api/lecturer/course/:courseId/students', authenticateToken, async (req, res) => {
    try {
        if (req.user.role !== 'lecturer') {
            return res.status(403).json({ success: false, error: 'Access denied. Lecturer only.' });
        }
        
        const { courseId } = req.params;
        
        // Verify lecturer owns this course
        const courseCheck = await pool.query(
            'SELECT * FROM courses WHERE id = $1 AND (lecturer_id = $2 OR $2 IN (SELECT id FROM users WHERE role = $3))',
            [courseId, req.user.id, 'admin']
        );
        
        if (courseCheck.rows.length === 0 && req.user.role !== 'admin') {
            return res.status(403).json({ success: false, error: 'You do not have access to this course' });
        }
        
        // Get all students enrolled in this course with their predictions
        const students = await pool.query(`
            SELECT 
                u.id as user_id,
                u.full_name,
                u.email,
                u.department,
                s.student_id,
                sc.enrolled_date,
                sc.semester,
                sc.academic_year,
                p.id as prediction_id,
                p.predicted_score,
                p.predicted_grade,
                p.recommendation,
                p.created_at as prediction_date
            FROM students s
            JOIN users u ON s.user_id = u.id
            JOIN student_courses sc ON s.id = sc.student_id
            JOIN courses c ON sc.course_id = c.id
            LEFT JOIN predictions p ON p.student_id = s.id AND p.course_code = c.course_code
            WHERE c.id = $1
            ORDER BY u.full_name
        `, [courseId]);
        
        // Get course details
        const course = await pool.query(
            'SELECT * FROM courses WHERE id = $1',
            [courseId]
        );
        
        res.json({
            success: true,
            course: course.rows[0],
            students: students.rows,
            count: students.rows.length
        });
        
    } catch (err) {
        console.error('Course students error:', err);
        res.status(500).json({ success: false, error: err.message });
    }
});

// Update student prediction (lecturer can add feedback)
app.put('/api/lecturer/prediction/:predictionId', authenticateToken, async (req, res) => {
    try {
        if (req.user.role !== 'lecturer') {
            return res.status(403).json({ success: false, error: 'Access denied. Lecturer only.' });
        }
        
        const { predictionId } = req.params;
        const { lecturer_feedback, predicted_score, predicted_grade } = req.body;
        
        const result = await pool.query(`
            UPDATE predictions 
            SET lecturer_feedback = COALESCE($1, lecturer_feedback),
                predicted_score = COALESCE($2, predicted_score),
                predicted_grade = COALESCE($3, predicted_grade),
                updated_by = $4,
                updated_at = NOW()
            WHERE id = $5
            RETURNING *
        `, [lecturer_feedback, predicted_score, predicted_grade, req.user.id, predictionId]);
        
        if (result.rows.length === 0) {
            return res.status(404).json({ success: false, error: 'Prediction not found' });
        }
        
        res.json({
            success: true,
            prediction: result.rows[0]
        });
        
    } catch (err) {
        console.error('Update prediction error:', err);
        res.status(500).json({ success: false, error: err.message });
    }
});

// Get course analytics
app.get('/api/lecturer/course/:courseId/analytics', authenticateToken, async (req, res) => {
    try {
        if (req.user.role !== 'lecturer') {
            return res.status(403).json({ success: false, error: 'Access denied. Lecturer only.' });
        }
        
        const { courseId } = req.params;
        
        const analytics = await pool.query(`
            SELECT 
                c.course_code,
                c.course_name,
                COUNT(DISTINCT s.id) as total_students,
                COUNT(p.id) as predictions_made,
                AVG(p.predicted_score) as average_score,
                COUNT(CASE WHEN p.predicted_grade = 'A' THEN 1 END) as grade_a_count,
                COUNT(CASE WHEN p.predicted_grade = 'B' THEN 1 END) as grade_b_count,
                COUNT(CASE WHEN p.predicted_grade = 'C' THEN 1 END) as grade_c_count,
                COUNT(CASE WHEN p.predicted_grade = 'D' THEN 1 END) as grade_d_count,
                COUNT(CASE WHEN p.predicted_grade = 'F' THEN 1 END) as grade_f_count
            FROM courses c
            LEFT JOIN student_courses sc ON c.id = sc.course_id
            LEFT JOIN students s ON sc.student_id = s.id
            LEFT JOIN predictions p ON p.student_id = s.id AND p.course_code = c.course_code
            WHERE c.id = $1
            GROUP BY c.id
        `, [courseId]);
        
        // Get grade distribution
        const gradeDistribution = await pool.query(`
            SELECT 
                p.predicted_grade,
                COUNT(*) as count
            FROM predictions p
            JOIN courses c ON p.course_code = c.course_code
            WHERE c.id = $1
            GROUP BY p.predicted_grade
            ORDER BY p.predicted_grade
        `, [courseId]);
        
        res.json({
            success: true,
            analytics: analytics.rows[0],
            grade_distribution: gradeDistribution.rows
        });
        
    } catch (err) {
        console.error('Course analytics error:', err);
        res.status(500).json({ success: false, error: err.message });
    }
});

// ============ LECTURER DASHBOARD ENDPOINTS ============

// Get lecturer dashboard data
app.get('/api/lecturer/dashboard', authenticateToken, async (req, res) => {
    try {
        console.log('Lecturer dashboard request - User:', req.user.id, 'Role:', req.user.role);
        
        // Check if user is a lecturer or admin
        if (req.user.role !== 'lecturer' && req.user.role !== 'admin') {
            return res.status(403).json({ 
                success: false, 
                error: 'Access denied. Lecturer or Admin only.' 
            });
        }
        
        // Get lecturer's courses with student counts
        const coursesResult = await pool.query(`
            SELECT 
                c.id,
                c.course_code,
                c.course_name,
                c.credits,
                COUNT(DISTINCT sc.student_id) as enrolled_students
            FROM courses c
            LEFT JOIN student_courses sc ON c.id = sc.course_id
            WHERE c.lecturer_id = $1
            GROUP BY c.id
            ORDER BY c.course_code
        `, [req.user.id]);
        
        // Get overall statistics
        const statsResult = await pool.query(`
            SELECT 
                COUNT(DISTINCT c.id) as total_courses,
                COUNT(DISTINCT sc.student_id) as total_students
            FROM courses c
            LEFT JOIN student_courses sc ON c.id = sc.course_id
            WHERE c.lecturer_id = $1
        `, [req.user.id]);
        
        res.json({
            success: true,
            courses: coursesResult.rows,
            stats: statsResult.rows[0] || { total_courses: 0, total_students: 0 },
            recent_predictions: []
        });
        
    } catch (err) {
        console.error('Lecturer dashboard error:', err);
        res.status(500).json({ success: false, error: err.message });
    }
});

// Get all students for a lecturer's course
app.get('/api/lecturer/course/:courseId/students', authenticateToken, async (req, res) => {
    try {
        if (req.user.role !== 'lecturer' && req.user.role !== 'admin') {
            return res.status(403).json({ success: false, error: 'Access denied' });
        }
        
        const { courseId } = req.params;
        
        // Get students enrolled in this course
        const students = await pool.query(`
            SELECT 
                u.id as user_id,
                u.full_name,
                u.email,
                u.department,
                s.student_id,
                sc.enrolled_date,
                sc.semester,
                sc.academic_year
            FROM students s
            JOIN users u ON s.user_id = u.id
            JOIN student_courses sc ON s.id = sc.student_id
            WHERE sc.course_id = $1
            ORDER BY u.full_name
        `, [courseId]);
        
        // Get course details
        const course = await pool.query(
            'SELECT * FROM courses WHERE id = $1',
            [courseId]
        );
        
        res.json({
            success: true,
            course: course.rows[0],
            students: students.rows,
            count: students.rows.length
        });
        
    } catch (err) {
        console.error('Course students error:', err);
        res.status(500).json({ success: false, error: err.message });
    }
});

// Get lecturer's courses list
app.get('/api/lecturer/courses', authenticateToken, async (req, res) => {
    try {
        if (req.user.role !== 'lecturer' && req.user.role !== 'admin') {
            return res.status(403).json({ success: false, error: 'Access denied' });
        }
        
        const courses = await pool.query(`
            SELECT 
                c.*,
                COUNT(DISTINCT sc.student_id) as enrolled_students
            FROM courses c
            LEFT JOIN student_courses sc ON c.id = sc.course_id
            WHERE c.lecturer_id = $1
            GROUP BY c.id
            ORDER BY c.course_code
        `, [req.user.id]);
        
        res.json({
            success: true,
            courses: courses.rows,
            count: courses.rows.length
        });
        
    } catch (err) {
        console.error('Lecturer courses error:', err);
        res.status(500).json({ success: false, error: err.message });
    }
});
