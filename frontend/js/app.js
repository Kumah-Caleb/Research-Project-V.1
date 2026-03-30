// app.js - Main application logic for USTED Predictor

// API Configuration
const API_BASE_URL = 'https://aamusted-predictor-backend2.onrender.com';

// Current user
let currentUser = null;

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    checkAuth();
    setupEventListeners();
});

// Check authentication status
async function checkAuth() {
    const token = localStorage.getItem('token');
    if (token) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/verify`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            if (response.ok) {
                currentUser = await response.json();
                updateUIForLoggedInUser();
            } else {
                logout();
            }
        } catch (error) {
            console.error('Auth check failed:', error);
            logout();
        }
    }
}

// Setup event listeners
function setupEventListeners() {
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }
    
    const predictionForm = document.getElementById('predictionForm');
    if (predictionForm) {
        predictionForm.addEventListener('submit', makePrediction);
    }
}

// Login function
async function handleLogin(event) {
    event.preventDefault();
    const email = document.getElementById('login-email')?.value;
    const password = document.getElementById('login-password')?.value;
    
    // Validate
    const emailResult = validateEmail(email);
    const passwordResult = validatePassword(password);
    
    if (!emailResult.isValid || !passwordResult.isValid) {
        showToast('Please enter valid credentials', 'error');
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
            currentUser = data.user;
            showToast('Login successful!', 'success');
            setTimeout(() => {
                window.location.href = 'student_dashboard.html';
            }, 1000);
        } else {
            showToast(data.message || 'Login failed', 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showToast('Network error. Please try again.', 'error');
    }
}

// Register function
async function handleRegister(event) {
    event.preventDefault();
    const name = document.getElementById('register-name')?.value;
    const email = document.getElementById('register-email')?.value;
    const studentId = document.getElementById('register-student-id')?.value;
    const password = document.getElementById('register-password')?.value;
    const confirmPassword = document.getElementById('register-confirm-password')?.value;
    
    // Validate
    const nameResult = validateName(name);
    const emailResult = validateEmail(email);
    const studentIdResult = validateStudentId(studentId);
    const passwordResult = validatePassword(password);
    const confirmResult = validateConfirmPassword(password, confirmPassword);
    
    if (!nameResult.isValid || !emailResult.isValid || !studentIdResult.isValid || 
        !passwordResult.isValid || !confirmResult.isValid) {
        showToast('Please fix validation errors', 'error');
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
            showToast('Registration successful! Please login.', 'success');
            setTimeout(() => {
                window.location.href = 'login.html';
            }, 1500);
        } else {
            showToast(data.message || 'Registration failed', 'error');
        }
    } catch (error) {
        console.error('Registration error:', error);
        showToast('Network error. Please try again.', 'error');
    }
}

// Make prediction
async function makePrediction(event) {
    event.preventDefault();
    
    const courseCode = document.getElementById('courseCode')?.value;
    const currentGrade = document.getElementById('currentGrade')?.value;
    const semester = document.getElementById('semester')?.value;
    const academicYear = document.getElementById('academicYear')?.value;
    const studyHours = document.getElementById('studyHours')?.value;
    const difficulty = document.getElementById('difficulty')?.value;
    const confidence = document.getElementById('confidence')?.value;
    
    // Validate
    const courseResult = validateCourseCode(courseCode);
    const semesterResult = validateSemester(semester);
    const yearResult = validateAcademicYear(academicYear);
    
    if (!courseResult.isValid || !semesterResult.isValid || !yearResult.isValid) {
        showToast('Please fix validation errors', 'error');
        return;
    }
    
    showLoading(true);
    
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE_URL}/api/predict`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                course_code: courseCode.toUpperCase(),
                current_grade: currentGrade,
                semester: parseInt(semester),
                academic_year: parseInt(academicYear),
                study_hours: parseInt(studyHours),
                difficulty: parseInt(difficulty),
                confidence: parseInt(confidence)
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displayPredictionResult(data);
            showToast('Prediction completed!', 'success');
        } else {
            showToast(data.message || 'Prediction failed', 'error');
        }
    } catch (error) {
        console.error('Prediction error:', error);
        showToast('Network error. Please try again.', 'error');
    } finally {
        showLoading(false);
    }
}

// Display prediction result
function displayPredictionResult(result) {
    const resultDiv = document.getElementById('predictionResult');
    const resultGrade = document.getElementById('resultGrade');
    const resultConfidence = document.getElementById('resultConfidence');
    const confidenceBar = document.getElementById('confidenceBar');
    const recommendations = document.getElementById('recommendations');
    
    resultGrade.textContent = result.predicted_grade;
    resultConfidence.textContent = result.confidence;
    confidenceBar.style.width = `${result.confidence}%`;
    
    // Generate recommendations based on grade
    let recText = '';
    if (result.predicted_grade === 'A' || result.predicted_grade === 'B+') {
        recText = 'Excellent! Keep up your study habits. Consider helping peers who may need assistance.';
    } else if (result.predicted_grade === 'B' || result.predicted_grade === 'C+') {
        recText = 'Good performance. Review challenging topics and maintain consistent study schedule.';
    } else if (result.predicted_grade === 'C' || result.predicted_grade === 'D+') {
        recText = 'You may need additional support. Consider attending tutorials and seeking help from lecturers.';
    } else {
        recText = 'Urgent action needed! Meet with your academic advisor and develop a study improvement plan.';
    }
    
    recommendations.textContent = recText;
    resultDiv.style.display = 'block';
    
    // Scroll to result
    resultDiv.scrollIntoView({ behavior: 'smooth' });
}

// Update UI for logged in user
function updateUIForLoggedInUser() {
    const welcomeMsg = document.getElementById('welcomeMessage');
    if (welcomeMsg && currentUser) {
        welcomeMsg.textContent = `Welcome back, ${currentUser.full_name || currentUser.name}!`;
    }
    loadDashboardData();
}

// Load dashboard data
async function loadDashboardData() {
    const token = localStorage.getItem('token');
    if (!token) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/dashboard/stats`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            document.getElementById('currentGpa').textContent = data.gpa || '3.45';
            document.getElementById('creditsCompleted').textContent = data.credits_completed || '72';
            document.getElementById('creditsRemaining').textContent = data.credits_remaining || '48';
            document.getElementById('coursesEnrolled').textContent = data.courses_enrolled || '5';
            
            const gpaPercent = (data.gpa / 4.0) * 100;
            document.getElementById('gpaProgress').style.width = `${gpaPercent}%`;
            document.getElementById('gpaProgress').textContent = `${Math.round(gpaPercent)}%`;
        }
        
        loadRecentPredictions();
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

// Load recent predictions
async function loadRecentPredictions() {
    const token = localStorage.getItem('token');
    const tbody = document.getElementById('recentPredictions');
    if (!tbody) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/predictions/recent`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        const predictions = await response.json();
        
        if (predictions && predictions.length > 0) {
            tbody.innerHTML = predictions.map(p => `
                <tr>
                    <td>${p.course_code}</td>
                    <td><span class="badge bg-primary">${p.predicted_grade}</span></td>
                    <td>${p.confidence}%</td>
                    <td>${new Date(p.created_at).toLocaleDateString()}</td>
                </tr>
            `).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center">No predictions yet. Make your first prediction!</td></tr>';
        }
    } catch (error) {
        console.error('Error loading predictions:', error);
        tbody.innerHTML = '<tr><td colspan="4" class="text-center">Error loading predictions</td></tr>';
    }
}

// Logout function
function logout() {
    localStorage.removeItem('token');
    currentUser = null;
    window.location.href = 'index.html';
}

// Show toast notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast-notification alert alert-${type === 'error' ? 'danger' : type}`;
    toast.textContent = message;
    toast.style.cssText = 'position: fixed; bottom: 20px; right: 20px; z-index: 9999; min-width: 250px;';
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

// Show/hide loading spinner
function showLoading(show) {
    let spinner = document.querySelector('.spinner-overlay');
    if (show) {
        if (!spinner) {
            spinner = document.createElement('div');
            spinner.className = 'spinner-overlay';
            spinner.innerHTML = '<div class="spinner"></div>';
            document.body.appendChild(spinner);
        }
        spinner.style.display = 'flex';
    } else if (spinner) {
        spinner.style.display = 'none';
    }
}

// Export functions for global use
window.handleLogin = handleLogin;
window.handleRegister = handleRegister;
window.makePrediction = makePrediction;
window.logout = logout;
