const { Pool } = require('pg');
const bcrypt = require('bcryptjs');
require('dotenv').config();

async function createLecturer() {
    const pool = new Pool({
        connectionString: process.env.DATABASE_URL,
        ssl: { rejectUnauthorized: false }
    });
    
    try {
        // Hash password for "lecturer123"
        const hashedPassword = await bcrypt.hash('lecturer123', 10);
        
        // Create lecturer user
        const result = await pool.query(`
            INSERT INTO users (full_name, username, email, password, role, department, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, NOW())
            ON CONFLICT (username) DO UPDATE SET
                role = EXCLUDED.role,
                password = EXCLUDED.password
            RETURNING id, full_name, username, role
        `, ['Dr. John Smith', 'drjohn', 'dr.john@aamusted.edu.gh', hashedPassword, 'lecturer', 'Computer Science']);
        
        console.log('✅ Lecturer account ready:');
        console.log(`   Username: drjohn`);
        console.log(`   Password: lecturer123`);
        console.log(`   Role: ${result.rows[0].role}`);
        
        // Check if there are any courses, and assign them to this lecturer if none have one
        const courses = await pool.query('SELECT id, course_code FROM courses WHERE lecturer_id IS NULL LIMIT 3');
        
        if (courses.rows.length > 0) {
            console.log(`\n📚 Assigning ${courses.rows.length} courses to lecturer:`);
            for (const course of courses.rows) {
                await pool.query('UPDATE courses SET lecturer_id = $1 WHERE id = $2', [result.rows[0].id, course.id]);
                console.log(`   - ${course.course_code}`);
            }
        } else {
            console.log('\n📚 No unassigned courses found. Create some courses first.');
        }
        
    } catch (err) {
        console.error('❌ Error:', err.message);
    } finally {
        await pool.end();
    }
}

createLecturer();
