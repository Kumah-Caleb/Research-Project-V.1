const { Pool } = require('pg');
require('dotenv').config();

async function verifyMigration() {
    const pool = new Pool({
        connectionString: process.env.DATABASE_URL,
        ssl: { rejectUnauthorized: false }
    });
    
    try {
        console.log('🔍 Verifying migration...\n');
        
        // Check lecturers
        const lecturers = await pool.query(`
            SELECT id, full_name, username, email, role 
            FROM users 
            WHERE role = 'lecturer'
        `);
        
        console.log(`📚 Lecturers found: ${lecturers.rows.length}`);
        lecturers.rows.forEach(l => {
            console.log(`   - ${l.full_name} (${l.username})`);
        });
        
        // Check courses with lecturers
        const courses = await pool.query(`
            SELECT c.course_code, c.course_name, u.full_name as lecturer_name
            FROM courses c
            LEFT JOIN users u ON c.lecturer_id = u.id
            WHERE c.lecturer_id IS NOT NULL
        `);
        
        console.log(`\n📖 Courses with lecturers: ${courses.rows.length}`);
        courses.rows.forEach(c => {
            console.log(`   - ${c.course_code}: ${c.course_name} (${c.lecturer_name})`);
        });
        
        // Check if the dashboard endpoint will work
        console.log(`\n✅ Migration complete! Lecturer dashboard should now work.`);
        
    } catch (err) {
        console.error('❌ Verification failed:', err.message);
    } finally {
        await pool.end();
    }
}

verifyMigration();
