// validation.js - Form validation with regex patterns for USTED

// Validation patterns
const VALIDATION_PATTERNS = {
    // Email pattern: standard email format with USTED domain
    email: /^[a-zA-Z0-9._%+-]+@(usted\.edu\.gh|[a-z]+\.usted\.edu\.gh)$/,
    
    // Password: at least 8 characters, 1 uppercase, 1 lowercase, 1 number
    password: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,}$/,
    
    // Student ID: 3 uppercase letters followed by 5-7 digits
    studentId: /^[A-Z]{3}\d{5,7}$/,
    
    // Name: letters, spaces, hyphens, apostrophes only (2-50 chars)
    name: /^[a-zA-Z\s\-']{2,50}$/,
    
    // Course code: 2-4 uppercase letters followed by 3-4 digits
    courseCode: /^[A-Z]{2,4}\d{3,4}$/,
    
    // Grade: A, B+, B, C+, C, D+, D, F only
    grade: /^(A|B\+|B|C\+|C|D\+|D|F)$/,
    
    // Semester: 1-8 only
    semester: /^[1-8]$/,
    
    // Academic year: 4 digits (2000-2030)
    academicYear: /^(20\d{2})$/
};

// Validation messages
const VALIDATION_MESSAGES = {
    email: 'Please enter a valid USTED email address (e.g., student@usted.edu.gh)',
    password: 'Password must be at least 8 characters with 1 uppercase, 1 lowercase, and 1 number',
    studentId: 'Student ID must be 3 uppercase letters followed by 5-7 digits (e.g., ITE12345)',
    name: 'Name must be 2-50 characters (letters, spaces, hyphens, apostrophes only)',
    courseCode: 'Course code must be 2-4 uppercase letters followed by 3-4 digits (e.g., ITE301)',
    grade: 'Please select a valid grade (A, B+, B, C+, C, D+, D, or F)',
    semester: 'Semester must be between 1 and 8',
    academicYear: 'Please enter a valid 4-digit year (e.g., 2024)',
    required: 'This field is required',
    confirmPassword: 'Passwords do not match'
};

// Validation functions
function validateEmail(email) {
    if (!email) return { isValid: false, message: VALIDATION_MESSAGES.required };
    if (!VALIDATION_PATTERNS.email.test(email)) {
        return { isValid: false, message: VALIDATION_MESSAGES.email };
    }
    return { isValid: true, message: '' };
}

function validatePassword(password) {
    if (!password) return { isValid: false, message: VALIDATION_MESSAGES.required };
    if (!VALIDATION_PATTERNS.password.test(password)) {
        return { isValid: false, message: VALIDATION_MESSAGES.password };
    }
    return { isValid: true, message: '' };
}

function validateStudentId(studentId) {
    if (!studentId) return { isValid: false, message: VALIDATION_MESSAGES.required };
    if (!VALIDATION_PATTERNS.studentId.test(studentId.toUpperCase())) {
        return { isValid: false, message: VALIDATION_MESSAGES.studentId };
    }
    return { isValid: true, message: '' };
}

function validateName(name) {
    if (!name) return { isValid: false, message: VALIDATION_MESSAGES.required };
    if (!VALIDATION_PATTERNS.name.test(name)) {
        return { isValid: false, message: VALIDATION_MESSAGES.name };
    }
    return { isValid: true, message: '' };
}

function validateCourseCode(courseCode) {
    if (!courseCode) return { isValid: false, message: VALIDATION_MESSAGES.required };
    if (!VALIDATION_PATTERNS.courseCode.test(courseCode.toUpperCase())) {
        return { isValid: false, message: VALIDATION_MESSAGES.courseCode };
    }
    return { isValid: true, message: '' };
}

function validateSemester(semester) {
    if (!semester) return { isValid: false, message: VALIDATION_MESSAGES.required };
    if (!VALIDATION_PATTERNS.semester.test(semester)) {
        return { isValid: false, message: VALIDATION_MESSAGES.semester };
    }
    return { isValid: true, message: '' };
}

function validateAcademicYear(year) {
    if (!year) return { isValid: false, message: VALIDATION_MESSAGES.required };
    const currentYear = new Date().getFullYear();
    if (!VALIDATION_PATTERNS.academicYear.test(year)) {
        return { isValid: false, message: VALIDATION_MESSAGES.academicYear };
    }
    if (year < 2000 || year > currentYear + 5) {
        return { isValid: false, message: `Year must be between 2000 and ${currentYear + 5}` };
    }
    return { isValid: true, message: '' };
}

function validateConfirmPassword(password, confirmPassword) {
    if (!confirmPassword) return { isValid: false, message: VALIDATION_MESSAGES.required };
    if (password !== confirmPassword) {
        return { isValid: false, message: VALIDATION_MESSAGES.confirmPassword };
    }
    return { isValid: true, message: '' };
}

// Helper function to show validation feedback
function showFieldValidation(inputElement, validationResult, errorElementId) {
    const errorElement = document.getElementById(errorElementId);
    
    if (!validationResult.isValid) {
        inputElement.classList.add('invalid');
        inputElement.classList.remove('valid');
        if (errorElement) {
            errorElement.textContent = validationResult.message;
            errorElement.style.display = 'block';
        }
    } else {
        inputElement.classList.add('valid');
        inputElement.classList.remove('invalid');
        if (errorElement) {
            errorElement.textContent = '';
            errorElement.style.display = 'none';
        }
    }
}

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { 
        validateEmail, validatePassword, validateStudentId, validateName,
        validateCourseCode, validateSemester, validateAcademicYear, 
        validateConfirmPassword, showFieldValidation 
    };
}
