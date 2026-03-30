// app.js - Main application for USTED Predictor

const API_BASE_URL = 'https://aamusted-predictor-backend2.onrender.com';
let currentUser = null;

document.addEventListener('DOMContentLoaded', function() {
    checkAuth();
});

async function checkAuth() {
    const token = localStorage.getItem('token');
    if (token) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/verify`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                currentUser = await response.json();
                updateUI();
                loadDashboardData();
            } else {
                logout();
            }
        } catch (error) {
            console.error('Auth error:', error);
        }
    }
}

function updateUI() {
    const welcomeMsg = document.getElementById('welcomeMessage');
    if (welcomeMsg && currentUser) {
        welcomeMsg.textContent = `Welcome back, ${currentUser.full_name || currentUser.name || 'Student'}!`;
    }
}

async function loadDashboardData() {
    const token = localStorage.getItem('token');
    if (!token) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/dashboard/stats`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            const gpaElement = document.getElementById('currentGpa');
            if (gpaElement) gpaElement.textContent = data.gpa || '3.45';
        }
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

function logout() {
    localStorage.removeItem('token');
    window.location.href = 'index.html';
}

// Set up logout button
document.addEventListener('DOMContentLoaded', function() {
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }
});

// Login function
window.handleLogin = async function(event) {
    event.preventDefault();
    const email = document.getElementById('login-email')?.value;
    const password = document.getElementById('login-password')?.value;
    
    const emailResult = validateEmail(email);
    const passwordResult = validatePassword(password);
    
    if (!emailResult.isValid || !passwordResult.isValid) {
        alert('Please enter valid credentials');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            localStorage.setItem('token', data.token);
            window.location.href = 'student_dashboard.html';
        } else {
            alert(data.message || 'Login failed');
        }
    } catch (error) {
        alert('Network error. Please try again.');
    }
};

// Register function
window.handleRegister = async function(event) {
    event.preventDefault();
    const name = document.getElementById('register-name')?.value;
    const email = document.getElementById('register-email')?.value;
    const studentId = document.getElementById('register-student-id')?.value;
    const password = document.getElementById('register-password')?.value;
    const confirmPassword = document.getElementById('register-confirm-password')?.value;
    
    const nameResult = validateName(name);
    const emailResult = validateEmail(email);
    const studentIdResult = validateStudentId(studentId);
    const passwordResult = validatePassword(password);
    
    if (!nameResult.isValid || !emailResult.isValid || !studentIdResult.isValid || !passwordResult.isValid) {
        alert('Please fix validation errors');
        return;
    }
    
    if (password !== confirmPassword) {
        alert('Passwords do not match');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, student_id: studentId, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('Registration successful! Please login.');
            window.location.href = 'login.html';
        } else {
            alert(data.message || 'Registration failed');
        }
    } catch (error) {
        alert('Network error. Please try again.');
    }
};
