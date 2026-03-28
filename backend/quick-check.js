const { Pool } = require('pg');
require('dotenv').config();

async function quickCheck() {
    const pool = new Pool({
        connectionString: process.env.DATABASE_URL,
        ssl: { rejectUnauthorized: false }
    });
    
    try {
        console.log('🔍 Quick Database Check\n');
        
        // Check users
        const users = await pool.query('SELECT id, username, role FROM users LIMIT 5');
        console.log('Users in database:');
        users.rows.forEach(u => console.log(`  - ${u.username} (${u.role})`));
        
        // Check if lecturer exists
        const lecturer = await pool.query("SELECT * FROM users WHERE role = 'lecturer'");
        if (lecturer.rows.length > 0) {
            console.log(`\n✅ Lecturer exists: ${lecturer.rows[0].username}`);
        } else {
            console.log('\n⚠️ No lecturer found. Creating one...');
            
            const bcrypt = require('bcryptjs');
            const hashedPassword = await bcrypt.hash('lecturer123', 10);
            
            const result = await pool.query(`
                INSERT INTO users (full_name, username, email, password, role, department)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (username) DO UPDATE SET role = EXCLUDED.role
                RETURNING id, username, role
            `, ['Dr. John Smith', 'drjohn', 'dr.john@aamusted.edu.gh', hashedPassword, 'lecturer', 'Computer Science']);
            
            console.log(`✅ Created lecturer: ${result.rows[0].username} with password: lecturer123`);
        }
        
        // Check courses
        const courses = await pool.query('SELECT id, course_code, lecturer_id FROM courses LIMIT 5');
        console.log(`\nCourses: ${courses.rows.length} found`);
        courses.rows.forEach(c => console.log(`  - ${c.course_code} (lecturer_id: ${c.lecturer_id || 'NULL'})`));
        
    } catch (err) {
        console.error('Error:', err.message);
    } finally {
        await pool.end();
    }
}

quickCheck();
