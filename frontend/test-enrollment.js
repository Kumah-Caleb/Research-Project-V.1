// test-enrollment.js
const API_URL = 'https://student-performance-predictor7.onrender.com';

async function testEnrollment() {
    console.log('=== Testing Enrollment System ===\n');
    
    // 1. Login as student
    console.log('1. Logging in as student...');
    const studentLogin = await fetch(`${API_URL}/api/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: 'Amoateng', password: 'student123' })
    });
    const student = await studentLogin.json();
    console.log(`   Student: ${student.user.full_name} (ID: ${student.user.id})`);
    
    // 2. Get available courses
    console.log('\n2. Getting available courses...');
    const coursesRes = await fetch(`${API_URL}/api/available_courses?user_id=${student.user.id}`);
    const courses = await coursesRes.json();
    console.log(`   Found ${courses.length} courses:`);
    courses.forEach(c => console.log(`     - ${c.code}: ${c.name} (ID: ${c.id})`));
    
    // 3. Enroll in first course
    if (courses.length > 0) {
        console.log('\n3. Enrolling in first course...');
        const enrollRes = await fetch(`${API_URL}/api/enroll`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                student_id: student.user.id, 
                course_id: courses[0].id 
            })
        });
        const enrollResult = await enrollRes.json();
        console.log(`   Result: ${enrollResult.success ? '✅ Success' : '❌ Failed: ' + enrollResult.error}`);
    }
    
    // 4. Login as lecturer
    console.log('\n4. Logging in as lecturer...');
    const lecturerLogin = await fetch(`${API_URL}/api/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: 'lecturer', password: 'lecturer123' })
    });
    const lecturer = await lecturerLogin.json();
    console.log(`   Lecturer: ${lecturer.user.full_name} (ID: ${lecturer.user.id})`);
    
    // 5. Get lecturer's students
    console.log('\n5. Getting lecturer\'s students...');
    const studentsRes = await fetch(`${API_URL}/api/my_students?lecturer_id=${lecturer.user.id}`);
    const students = await studentsRes.json();
    console.log(`   Found ${students.length} students:`);
    students.forEach(s => {
        console.log(`     - ${s.full_name} (${s.index_number})`);
        console.log(`       Courses: ${s.courses.map(c => c.code).join(', ')}`);
    });
}

testEnrollment().catch(console.error);
