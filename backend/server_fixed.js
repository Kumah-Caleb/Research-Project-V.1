// Make prediction - FIXED VERSION
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

// Get student's prediction history - FIXED VERSION
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

// Dashboard statistics - FIXED VERSION
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
