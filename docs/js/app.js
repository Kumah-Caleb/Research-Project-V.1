// app.js - Complete USTED Predictor Application
// Backend URL
const API_BASE_URL = 'https://aamusted-predictor-backend2.onrender.com';
let currentUser = null;

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    checkAuth();
    setupEventListeners();
    setupRangeSliders();
});

function setupEventListeners() {
    // Logout button
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }
    
    // Prediction form
    const predictionForm = document.getElementById('predictionForm');
    if (predictionForm) {
        predictionForm.addEventListener('submit', makePrediction);
    }
    
    // Login form
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    // Register form
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }
    
    // Profile form
    const profileForm = document.getElementById('profileForm');
    if (profileForm) {
        profileForm.addEventListener('submit', updateProfile);
    }
    
    // Quick prediction button
    const quickPredictBtn = document.getElementById('quickPredictBtn');
    if (quickPredictBtn) {
        quickPredictBtn.addEventListener('click', function() {
            window.location.href = 'predictor.html';
        });
    }
}

function setupRangeSliders() {
    // Study hours slider
    const studyHours = document.getElementById('studyHours');
    if (studyHours) {
        studyHours.addEventListener('input', function() {
            const value = this.value;
            const display = document.getElementById('studyHoursValue');
            if (display) display.textContent = value + ' hours';
        });
    }
    
    // Difficulty slider
    const difficulty = document.getElementById('difficulty');
    if (difficulty) {
        difficulty.addEventListener('input', function() {
            const value = parseInt(this.value);
            const texts = ['Easy', 'Fairly Easy', 'Medium', 'Challenging', 'Very Hard'];
            const display = document.getElementById('difficultyValue');
            if (display) display.textContent = texts[value-1] + ' (' + value + '/5)';
        });
    }
    
    // Confidence slider
    const confidence = document.getElementById('confidence');
    if (confidence) {
        confidence.addEventListener('input', function() {
            const value = parseInt(this.value);
            const texts = ['Very Low', 'Low', 'Moderate', 'High', 'Very High'];
            const display = document.getElementById('confidenceValue');
            if (display) display.textContent = texts[value-1] + ' (' + value + '/5)';
        });
    }
}

// ============================================
// AUTHENTICATION
// ============================================

async function checkAuth() {
    const token = localStorage.getItem('token');
    if (token) {
        showLoading(true);
        try {
            const response = await fetch(`${API_BASE_URL}/api/verify?token=${token}`);
            if (response.ok) {
                currentUser = await response.json();
                updateUI();
                if (window.loadDashboardData) {
                    await loadDashboardData();
                }
                if (window.loadRecentPredictions) {
                    await loadRecentPredictions();
                }
                if (window.loadHistory) {
                    await loadHistory();
                }
                if (window.loadProfile) {
                    await loadProfile();
                }
            } else {
                logout();
            }
        } catch (error) {
            console.error('Auth error:', error);
            logout();
        } finally {
            showLoading(false);
        }
    }
}

function updateUI() {
    const welcomeMsg = document.getElementById('welcomeMessage');
    if (welcomeMsg && currentUser) {
        welcomeMsg.textContent = `Welcome back, ${currentUser.full_name || currentUser.username || 'Student'}!`;
    }
    
    // Update profile page if on profile page
    const profileName = document.getElementById('profile-name');
    const profileEmail = document.getElementById('profile-email');
    const profileStudentId = document.getElementById('profile-student-id');
    
    if (profileName && currentUser) {
        profileName.value = currentUser.full_name || '';
    }
    if (profileEmail && currentUser) {
        profileEmail.value = currentUser.email || '';
    }
    if (profileStudentId && currentUser) {
        profileStudentId.value = currentUser.student_id || '';
    }
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    currentUser = null;
    window.location.href = 'index.html';
}

// ============================================
// LOGIN HANDLER
// ============================================

async function handleLogin(event) {
    if (event) event.preventDefault();
    
    const username = document.getElementById('login-username')?.value;
    const password = document.getElementById('login-password')?.value;
    
    if (!username || !password) {
        showToast('Please enter username and password', 'error');
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            localStorage.setItem('token', data.token);
            localStorage.setItem('user', JSON.stringify(data.user));
            currentUser = data.user;
            showToast('Login successful! Redirecting...', 'success');
            setTimeout(() => {
                window.location.href = 'student_dashboard.html';
            }, 1000);
        } else {
            showToast(data.detail || 'Invalid username or password', 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showToast('Network error. Please try again.', 'error');
    } finally {
        showLoading(false);
    }
}

// ============================================
// REGISTRATION HANDLER
// ============================================

async function handleRegister(event) {
    if (event) event.preventDefault();
    
    const name = document.getElementById('register-name')?.value;
    const username = document.getElementById('register-username')?.value;
    const email = document.getElementById('register-email')?.value;
    const studentId = document.getElementById('register-student-id')?.value;
    const password = document.getElementById('register-password')?.value;
    const confirmPassword = document.getElementById('register-confirm-password')?.value;
    
    // Validate all fields
    const nameResult = validateName(name);
    const usernameResult = validateUsername ? validateUsername(username) : { isValid: true, message: '' };
    const emailResult = validateEmail(email);
    const studentIdResult = validateStudentId(studentId);
    const passwordResult = validatePassword(password);
    
    let hasError = false;
    
    if (!nameResult.isValid) {
        document.getElementById('register-name-error').textContent = nameResult.message;
        hasError = true;
    } else {
        document.getElementById('register-name-error').textContent = '';
    }
    
    if (usernameResult && !usernameResult.isValid) {
        document.getElementById('register-username-error').textContent = usernameResult.message;
        hasError = true;
    } else if (document.getElementById('register-username-error')) {
        document.getElementById('register-username-error').textContent = '';
    }
    
    if (!emailResult.isValid) {
        document.getElementById('register-email-error').textContent = emailResult.message;
        hasError = true;
    } else {
        document.getElementById('register-email-error').textContent = '';
    }
    
    if (!studentIdResult.isValid) {
        document.getElementById('register-studentid-error').textContent = studentIdResult.message;
        hasError = true;
    } else {
        document.getElementById('register-studentid-error').textContent = '';
    }
    
    if (!passwordResult.isValid) {
        document.getElementById('register-password-error').textContent = passwordResult.message;
        hasError = true;
    } else {
        document.getElementById('register-password-error').textContent = '';
    }
    
    if (password !== confirmPassword) {
        document.getElementById('register-confirm-error').textContent = 'Passwords do not match';
        hasError = true;
    } else {
        document.getElementById('register-confirm-error').textContent = '';
    }
    
    if (hasError) {
        showToast('Please fix the errors above', 'error');
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                username: username,
                full_name: name, 
                email, 
                student_id: studentId, 
                password 
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Show success modal if it exists
            const overlay = document.getElementById('successOverlay');
            const modal = document.getElementById('successModal');
            if (overlay && modal) {
                overlay.style.display = 'block';
                modal.style.display = 'block';
                setTimeout(() => {
                    window.location.href = 'login.html';
                }, 3000);
            } else {
                showToast('Registration successful! Redirecting to login...', 'success');
                setTimeout(() => {
                    window.location.href = 'login.html';
                }, 2000);
            }
        } else {
            showToast(data.detail || data.message || 'Registration failed', 'error');
        }
    } catch (error) {
        console.error('Registration error:', error);
        showToast('Network error. Please try again.', 'error');
    } finally {
        showLoading(false);
    }
}

// ============================================
// PREDICTION FUNCTIONS
// ============================================

async function makePrediction(event) {
    if (event) event.preventDefault();
    
    const courseCode = document.getElementById('courseCode')?.value;
    const currentGrade = document.getElementById('currentGrade')?.value;
    const semester = document.getElementById('semester')?.value;
    const academicYear = document.getElementById('academicYear')?.value;
    const studyHours = document.getElementById('studyHours')?.value || 10;
    const difficulty = document.getElementById('difficulty')?.value || 3;
    const confidence = document.getElementById('confidence')?.value || 3;
    
    // Validate course code
    const courseResult = validateCourseCode(courseCode);
    if (!courseResult.isValid) {
        const errorDiv = document.getElementById('courseCodeError');
        if (errorDiv) errorDiv.textContent = courseResult.message;
        return;
    } else {
        const errorDiv = document.getElementById('courseCodeError');
        if (errorDiv) errorDiv.textContent = '';
    }
    
    // Validate semester
    if (!semester) {
        showToast('Please select a semester', 'error');
        return;
    }
    
    // Validate academic year
    if (!academicYear || academicYear.length !== 4) {
        showToast('Please enter a valid 4-digit academic year', 'error');
        return;
    }
    
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = 'login.html';
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/predict?token=${token}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
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
            // Display results
            const resultDiv = document.getElementById('predictionResult');
            const resultGrade = document.getElementById('resultGrade');
            const resultConfidence = document.getElementById('resultConfidence');
            const confidenceBar = document.getElementById('confidenceBar');
            const recommendations = document.getElementById('recommendations');
            
            if (resultGrade) resultGrade.textContent = data.predicted_grade;
            if (resultConfidence) resultConfidence.textContent = data.confidence;
            if (confidenceBar) confidenceBar.style.width = `${data.confidence}%`;
            if (recommendations) recommendations.textContent = data.recommendations;
            if (resultDiv) resultDiv.style.display = 'block';
            
            showToast('Prediction completed!', 'success');
            
            // Scroll to result
            if (resultDiv) resultDiv.scrollIntoView({ behavior: 'smooth' });
        } else {
            showToast(data.detail || data.message || 'Prediction failed', 'error');
        }
    } catch (error) {
        console.error('Prediction error:', error);
        showToast('Network error. Please try again.', 'error');
    } finally {
        showLoading(false);
    }
}

// ============================================
// DASHBOARD FUNCTIONS
// ============================================

async function loadDashboardData() {
    const token = localStorage.getItem('token');
    if (!token) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/dashboard/stats?token=${token}`);
        const data = await response.json();
        
        if (response.ok) {
            const gpaElement = document.getElementById('currentGpa');
            if (gpaElement) gpaElement.textContent = data.gpa || '3.45';
            
            const creditsElement = document.getElementById('creditsCompleted');
            if (creditsElement) creditsElement.textContent = data.credits_completed || '72';
            
            const remainingElement = document.getElementById('creditsRemaining');
            if (remainingElement) remainingElement.textContent = data.credits_remaining || '48';
            
            const coursesElement = document.getElementById('coursesEnrolled');
            if (coursesElement) coursesElement.textContent = data.courses_enrolled || '5';
            
            const gpaProgress = document.getElementById('gpaProgress');
            if (gpaProgress) {
                const gpaPercent = ((data.gpa || 3.45) / 4.0) * 100;
                gpaProgress.style.width = `${gpaPercent}%`;
                gpaProgress.textContent = `${Math.round(gpaPercent)}%`;
            }
        }
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

async function loadRecentPredictions() {
    const token = localStorage.getItem('token');
    const tbody = document.getElementById('recentPredictions');
    if (!tbody) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/predictions/recent?token=${token}`);
        const predictions = await response.json();
        
        if (response.ok && predictions && predictions.length > 0) {
            tbody.innerHTML = predictions.map(p => `
                <tr>
                    <td><strong>${p.course_code}</strong></td>
                    <td><span class="badge bg-primary">${p.predicted_grade}</span></td>
                    <td>${p.confidence}%</td>
                    <td>${new Date(p.created_at).toLocaleDateString()}</td>
                </tr>
            `).join('');
            
            // Update predictions count
            const predCount = document.getElementById('predictionsMade');
            if (predCount) predCount.textContent = predictions.length;
        } else {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center">No predictions yet. Make your first prediction!</td></tr>';
        }
    } catch (error) {
        console.error('Error loading predictions:', error);
        tbody.innerHTML = '<tr><td colspan="4" class="text-center">Error loading predictions</td></tr>';
    }
}

async function loadHistory() {
    const token = localStorage.getItem('token');
    const tbody = document.getElementById('historyTable');
    if (!tbody) return;
    
    tbody.innerHTML = '<tr><td colspan="6" class="text-center">Loading...</td></tr>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/predictions/history?token=${token}`);
        const predictions = await response.json();
        
        if (response.ok && predictions && predictions.length > 0) {
            tbody.innerHTML = predictions.map(p => `
                <tr>
                    <td><strong>${p.course_code}</strong></td>
                    <td><span class="badge bg-primary">${p.predicted_grade}</span></td>
                    <td>
                        <div class="progress" style="height: 20px;">
                            <div class="progress-bar bg-info" style="width: ${p.confidence}%">
                                ${p.confidence}%
                            </div>
                        </div>
                    </td>
                    <td>${p.actual_grade || '<span class="text-muted">Pending</span>'}</td>
                    <td>${new Date(p.created_at).toLocaleDateString()}</td>
                    <td>${p.actual_grade ? '✅ Completed' : '⏳ Pending'}</td>
                </tr>
            `).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">No predictions yet. Make your first prediction!</td></tr>';
        }
    } catch (error) {
        console.error('Error loading history:', error);
        tbody.innerHTML = '<tr><td colspan="6" class="text-center">Error loading history</td></tr>';
    }
}

// ============================================
// PROFILE FUNCTIONS
// ============================================

async function loadProfile() {
    const token = localStorage.getItem('token');
    if (!token) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/profile?token=${token}`);
        const user = await response.json();
        
        if (response.ok) {
            const nameField = document.getElementById('profile-name');
            const emailField = document.getElementById('profile-email');
            const studentIdField = document.getElementById('profile-student-id');
            const memberSince = document.getElementById('memberSince');
            const predictionsCount = document.getElementById('predictionsCount');
            
            if (nameField) nameField.value = user.full_name || '';
            if (emailField) emailField.value = user.email || '';
            if (studentIdField) studentIdField.value = user.student_id || '';
            if (memberSince && user.created_at) {
                memberSince.textContent = new Date(user.created_at).toLocaleDateString();
            }
            if (predictionsCount) predictionsCount.textContent = user.predictions_count || 0;
        }
    } catch (error) {
        console.error('Error loading profile:', error);
    }
}

async function updateProfile(event) {
    if (event) event.preventDefault();
    
    const newName = document.getElementById('profile-name')?.value;
    const nameResult = validateName(newName);
    
    if (!nameResult.isValid) {
        const errorDiv = document.getElementById('name-error');
        if (errorDiv) errorDiv.textContent = nameResult.message;
        return;
    }
    
    const token = localStorage.getItem('token');
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/profile/update?token=${token}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ full_name: newName })
        });
        
        if (response.ok) {
            showToast('Profile updated successfully!', 'success');
            if (currentUser) currentUser.full_name = newName;
        } else {
            showToast('Update failed', 'error');
        }
    } catch (error) {
        console.error('Error updating profile:', error);
        showToast('Network error', 'error');
    } finally {
        showLoading(false);
    }
}

// ============================================
// UI HELPER FUNCTIONS
// ============================================

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

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast-notification alert alert-${type === 'error' ? 'danger' : type}`;
    toast.textContent = message;
    toast.style.cssText = 'position: fixed; bottom: 20px; right: 20px; z-index: 10000; min-width: 250px; padding: 12px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);';
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

// ============================================
// EXPORT FUNCTIONS FOR GLOBAL ACCESS
// ============================================

window.handleLogin = handleLogin;
window.handleRegister = handleRegister;
window.makePrediction = makePrediction;
window.logout = logout;
window.loadDashboardData = loadDashboardData;
window.loadRecentPredictions = loadRecentPredictions;
window.loadHistory = loadHistory;
window.loadProfile = loadProfile;
window.updateProfile = updateProfile;
window.showToast = showToast;
window.showLoading = showLoading;
