// API Configuration
const API_BASE_URL = 'https://aamusted-predictor-backend2.onrender.com';
let currentUser = null;
let authToken = null;

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
});

// Check authentication status
function checkAuth() {
    const token = localStorage.getItem('token');
    const user = localStorage.getItem('user');
    
    if (token && user) {
        authToken = token;
        currentUser = JSON.parse(user);
        showPage('dashboard');
        loadDashboard();
        loadUserProfile();
    } else {
        showLogin();
    }
}

// Show login page
function showLogin() {
    showPage('loginPage');
    document.getElementById('loginForm').reset();
}

// Show register page
function showRegister() {
    showPage('registerPage');
    document.getElementById('registerForm').reset();
}

// Handle login
async function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            authToken = data.token;
            currentUser = data.user;
            
            localStorage.setItem('token', authToken);
            localStorage.setItem('user', JSON.stringify(currentUser));
            
            showToast('Login successful! Welcome back!', 'success');
            showPage('dashboard');
            loadDashboard();
            loadUserProfile();
        } else {
            showToast(data.error || 'Login failed', 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showToast('Network error. Please try again.', 'error');
    } finally {
        hideLoading();
    }
}

// Handle registration
async function handleRegister(event) {
    event.preventDefault();
    
    const userData = {
        full_name: document.getElementById('regFullName').value,
        username: document.getElementById('regUsername').value,
        email: document.getElementById('regEmail').value,
        password: document.getElementById('regPassword').value,
        department: document.getElementById('regDepartment').value
    };
    
    if (userData.password.length < 6) {
        showToast('Password must be at least 6 characters', 'error');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(userData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            authToken = data.token;
            currentUser = data.user;
            
            localStorage.setItem('token', authToken);
            localStorage.setItem('user', JSON.stringify(currentUser));
            
            showToast('Registration successful! Welcome!', 'success');
            showPage('dashboard');
            loadDashboard();
            loadUserProfile();
        } else {
            showToast(data.error || 'Registration failed', 'error');
        }
    } catch (error) {
        console.error('Registration error:', error);
        showToast('Network error. Please try again.', 'error');
    } finally {
        hideLoading();
    }
}

// Load dashboard data
async function loadDashboard() {
    if (!authToken) return;
    
    showLoading();
    
    try {
        // Load dashboard stats
        const statsResponse = await fetch(`${API_BASE_URL}/api/dashboard/stats`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        const statsData = await statsResponse.json();
        
        if (statsData.success) {
            // Update stats
            document.getElementById('totalCourses').textContent = statsData.stats.total_courses || 0;
            document.getElementById('avgScore').textContent = Math.round(statsData.stats.avg_score || 0) + '%';
            document.getElementById('highPerformance').textContent = statsData.stats.high_performance || 0;
            document.getElementById('atRisk').textContent = statsData.stats.at_risk || 0;
            
            // Display recent predictions
            if (statsData.recent_predictions && statsData.recent_predictions.length > 0) {
                displayRecentPredictions(statsData.recent_predictions);
            } else {
                document.getElementById('recentPredictions').innerHTML = '<p>No predictions yet. Make your first prediction!</p>';
            }
        }
        
        // Also load courses for the courses page
        await loadCourses();
        
    } catch (error) {
        console.error('Dashboard error:', error);
        showToast('Failed to load dashboard data', 'error');
    } finally {
        hideLoading();
    }
}

// Display recent predictions on dashboard
function displayRecentPredictions(predictions) {
    const container = document.getElementById('recentPredictions');
    
    if (!predictions || predictions.length === 0) {
        container.innerHTML = '<p>No predictions yet. Make your first prediction!</p>';
        return;
    }
    
    container.innerHTML = predictions.map(pred => `
        <div class="history-item">
            <div class="history-course">
                <strong>${pred.course_code}</strong> - ${pred.course_name}
                <div><small>${new Date(pred.created_at).toLocaleDateString()}</small></div>
            </div>
            <div>
                <span class="history-score">${pred.predicted_score}%</span>
                <span class="history-grade grade-${pred.predicted_grade}">${pred.predicted_grade}</span>
            </div>
        </div>
    `).join('');
}

// Load user courses
async function loadCourses() {
    if (!authToken) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/student/${currentUser.id}/courses`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayCourses(data.courses);
        }
    } catch (error) {
        console.error('Courses error:', error);
    }
}

// Display courses
function displayCourses(courses) {
    const container = document.getElementById('coursesList');
    
    if (!courses || courses.length === 0) {
        container.innerHTML = '<p>No courses found. Please contact your academic advisor.</p>';
        return;
    }
    
    container.innerHTML = courses.map(course => `
        <div class="course-card">
            <h3>${course.course_name}</h3>
            <div class="course-code">${course.course_code}</div>
            <div class="course-credits">${course.credits} Credits</div>
            <div class="course-semester">Semester ${course.semester || 'N/A'}</div>
            <button onclick="showPredictionForm('${course.course_code}', '${course.course_name}', ${course.credits})" class="btn-predict" style="margin-top: 1rem; padding: 0.5rem;">
                Predict Performance
            </button>
        </div>
    `).join('');
}

// Filter courses
function filterCourses() {
    const searchTerm = document.getElementById('courseSearch').value.toLowerCase();
    const semester = document.getElementById('semesterFilter').value;
    
    const courses = document.querySelectorAll('.course-card');
    
    courses.forEach(course => {
        const name = course.querySelector('h3').textContent.toLowerCase();
        const code = course.querySelector('.course-code').textContent.toLowerCase();
        const courseSemester = course.querySelector('.course-semester')?.textContent || '';
        
        const matchesSearch = name.includes(searchTerm) || code.includes(searchTerm);
        const matchesSemester = !semester || courseSemester.includes(semester);
        
        course.style.display = matchesSearch && matchesSemester ? 'block' : 'none';
    });
}

// Load prediction history
async function loadPredictionHistory() {
    if (!authToken) return;
    
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/student/${currentUser.id}/predictions`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        const data = await response.json();
        
        if (data.success && data.predictions) {
            displayPredictionHistory(data.predictions);
        } else {
            document.getElementById('predictionHistory').innerHTML = '<p>No predictions yet. Make your first prediction!</p>';
        }
    } catch (error) {
        console.error('History error:', error);
        showToast('Failed to load prediction history', 'error');
    } finally {
        hideLoading();
    }
}

// Display prediction history
function displayPredictionHistory(predictions) {
    const container = document.getElementById('predictionHistory');
    
    if (!predictions || predictions.length === 0) {
        container.innerHTML = '<p>No predictions yet. Start by making a prediction!</p>';
        return;
    }
    
    container.innerHTML = predictions.map(pred => `
        <div class="history-item">
            <div class="history-course">
                <strong>${pred.course_code}</strong> - ${pred.course_name}
                <div class="course-credits">${pred.credits} Credits</div>
                <small>${new Date(pred.created_at).toLocaleDateString()} at ${new Date(pred.created_at).toLocaleTimeString()}</small>
            </div>
            <div>
                <span class="history-score">${pred.predicted_score}%</span>
                <span class="history-grade grade-${pred.predicted_grade}">${pred.predicted_grade}</span>
            </div>
        </div>
    `).join('');
}

// Make prediction
async function makePrediction(event) {
    event.preventDefault();
    
    const predictionData = {
        student_id: currentUser.id,
        course_code: document.getElementById('courseCode').value,
        course_name: document.getElementById('courseName').value,
        credits: parseInt(document.getElementById('credits').value),
        semester: document.getElementById('semester').value,
        academic_year: new Date().getFullYear().toString()
    };
    
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/predict`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(predictionData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayPredictionResult(data.prediction);
            document.getElementById('predictionForm').reset();
            
            // Refresh all data
            await loadPredictionHistory();
            await loadDashboard();
            
            showToast('Prediction generated successfully!', 'success');
        } else {
            showToast(data.error || 'Prediction failed', 'error');
        }
    } catch (error) {
        console.error('Prediction error:', error);
        showToast('Network error. Please try again.', 'error');
    } finally {
        hideLoading();
    }
}

// Display prediction result
function displayPredictionResult(prediction) {
    const container = document.getElementById('predictionResult');
    
    container.innerHTML = `
        <div class="prediction-card">
            <h3>Prediction Result</h3>
            <div><strong>${prediction.course_code}</strong> - ${prediction.course_name}</div>
            <div class="prediction-score">${prediction.predicted_score}%</div>
            <div class="prediction-grade grade-${prediction.predicted_grade}">Grade: ${prediction.predicted_grade}</div>
            <div class="prediction-recommendation">
                <strong>Recommendation:</strong> ${prediction.recommendation}
            </div>
        </div>
    `;
    
    // Scroll to result
    container.scrollIntoView({ behavior: 'smooth' });
}

// Load user profile
async function loadUserProfile() {
    if (!authToken || !currentUser) return;
    
    document.getElementById('userName').textContent = currentUser.full_name;
    document.getElementById('profileFullName').textContent = currentUser.full_name;
    document.getElementById('profileUsername').textContent = currentUser.username;
    document.getElementById('profileEmail').textContent = currentUser.email;
    document.getElementById('profileDepartment').textContent = currentUser.department || 'Not specified';
    document.getElementById('profileJoined').textContent = new Date().toLocaleDateString();
}

// Show prediction form with course data
function showPredictionForm(courseCode, courseName, credits) {
    showPage('predictionsPage');
    document.getElementById('courseCode').value = courseCode;
    document.getElementById('courseName').value = courseName;
    document.getElementById('credits').value = credits;
    document.getElementById('predictionResult').innerHTML = '';
    
    // Also load prediction history
    loadPredictionHistory();
    
    // Scroll to form
    document.querySelector('.prediction-form').scrollIntoView({ behavior: 'smooth' });
}

// Logout
function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    authToken = null;
    currentUser = null;
    showLogin();
    showToast('Logged out successfully', 'info');
}

// Show page
function showPage(pageId) {
    const pages = document.querySelectorAll('.page');
    pages.forEach(page => {
        page.classList.remove('active');
    });
    
    document.getElementById(pageId).classList.add('active');
    
    // Load page-specific data
    if (pageId === 'dashboardPage') {
        loadDashboard();
    } else if (pageId === 'coursesPage') {
        loadCourses();
    } else if (pageId === 'predictionsPage') {
        loadPredictionHistory();
    } else if (pageId === 'profilePage') {
        loadUserProfile();
    }
}

// Toggle mobile menu
function toggleMobileMenu() {
    const navLinks = document.getElementById('navLinks');
    navLinks.classList.toggle('active');
}

// Show toast notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// Loading indicators
function showLoading() {
    let loader = document.querySelector('.loading-overlay');
    if (!loader) {
        loader = document.createElement('div');
        loader.className = 'loading-overlay';
        loader.innerHTML = '<div class="spinner"></div>';
        document.body.appendChild(loader);
    }
    loader.style.display = 'flex';
}

function hideLoading() {
    const loader = document.querySelector('.loading-overlay');
    if (loader) {
        loader.style.display = 'none';
    }
}
