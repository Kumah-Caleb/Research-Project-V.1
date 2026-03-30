// validation.js - Form validation utilities

// Regex patterns for validation
const VALIDATION_PATTERNS = {
    // Email pattern: standard email format
    email: /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/,
    
    // Password: at least 8 characters, 1 uppercase, 1 lowercase, 1 number
    password: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,}$/,
    
    // Student ID: 3 uppercase letters followed by 5-7 digits
    studentId: /^[A-Z]{3}\d{5,7}$/,
    
    // Name: letters, spaces, hyphens, apostrophes only (2-50 chars)
    name: /^[a-zA-Z\s\-']{2,50}$/,
    
    // Course code: 2-4 uppercase letters followed by 3-4 digits
    courseCode: /^[A-Z]{2,4}\d{3,4}$/,
    
    // Grade: A, B+, B, C+, C, D+, D, F only
    grade: /^[A-D][+]?|F$/,
    
    // Semester: 1-8 only
    semester: /^[1-8]$/,
    
    // Academic year: 4 digits
    academicYear: /^\d{4}$/
};

// Validation messages
const VALIDATION_MESSAGES = {
    email: 'Please enter a valid email address (e.g., name@domain.com)',
    password: 'Password must be at least 8 characters with 1 uppercase, 1 lowercase, and 1 number',
    studentId: 'Student ID must be 3 uppercase letters followed by 5-7 digits (e.g., STU12345)',
    name: 'Name must be 2-50 characters (letters, spaces, hyphens, apostrophes only)',
    courseCode: 'Course code must be 2-4 uppercase letters followed by 3-4 digits (e.g., CS101)',
    grade: 'Please enter a valid grade (A, B+, B, C+, C, D+, D, or F)',
    semester: 'Semester must be between 1 and 8',
    academicYear: 'Please enter a valid 4-digit year (e.g., 2024)',
    required: 'This field is required',
    confirmPassword: 'Passwords do not match'
};

// Validation functions
const Validator = {
    // Validate email
    validateEmail: (email) => {
        if (!email) return { isValid: false, message: VALIDATION_MESSAGES.required };
        if (!VALIDATION_PATTERNS.email.test(email)) {
            return { isValid: false, message: VALIDATION_MESSAGES.email };
        }
        return { isValid: true, message: '' };
    },
    
    // Validate password
    validatePassword: (password) => {
        if (!password) return { isValid: false, message: VALIDATION_MESSAGES.required };
        if (!VALIDATION_PATTERNS.password.test(password)) {
            return { isValid: false, message: VALIDATION_MESSAGES.password };
        }
        return { isValid: true, message: '' };
    },
    
    // Validate student ID
    validateStudentId: (studentId) => {
        if (!studentId) return { isValid: false, message: VALIDATION_MESSAGES.required };
        if (!VALIDATION_PATTERNS.studentId.test(studentId)) {
            return { isValid: false, message: VALIDATION_MESSAGES.studentId };
        }
        return { isValid: true, message: '' };
    },
    
    // Validate name
    validateName: (name) => {
        if (!name) return { isValid: false, message: VALIDATION_MESSAGES.required };
        if (!VALIDATION_PATTERNS.name.test(name)) {
            return { isValid: false, message: VALIDATION_MESSAGES.name };
        }
        return { isValid: true, message: '' };
    },
    
    // Validate course code
    validateCourseCode: (courseCode) => {
        if (!courseCode) return { isValid: false, message: VALIDATION_MESSAGES.required };
        if (!VALIDATION_PATTERNS.courseCode.test(courseCode)) {
            return { isValid: false, message: VALIDATION_MESSAGES.courseCode };
        }
        return { isValid: true, message: '' };
    },
    
    // Validate grade
    validateGrade: (grade) => {
        if (!grade) return { isValid: false, message: VALIDATION_MESSAGES.required };
        if (!VALIDATION_PATTERNS.grade.test(grade)) {
            return { isValid: false, message: VALIDATION_MESSAGES.grade };
        }
        return { isValid: true, message: '' };
    },
    
    // Validate semester
    validateSemester: (semester) => {
        if (!semester) return { isValid: false, message: VALIDATION_MESSAGES.required };
        if (!VALIDATION_PATTERNS.semester.test(semester.toString())) {
            return { isValid: false, message: VALIDATION_MESSAGES.semester };
        }
        return { isValid: true, message: '' };
    },
    
    // Validate academic year
    validateAcademicYear: (year) => {
        if (!year) return { isValid: false, message: VALIDATION_MESSAGES.required };
        if (!VALIDATION_PATTERNS.academicYear.test(year.toString())) {
            return { isValid: false, message: VALIDATION_MESSAGES.academicYear };
        }
        const currentYear = new Date().getFullYear();
        if (year < 2000 || year > currentYear + 5) {
            return { isValid: false, message: Year must be between 2000 and  };
        }
        return { isValid: true, message: '' };
    },
    
    // Validate confirm password
    validateConfirmPassword: (password, confirmPassword) => {
        if (!confirmPassword) return { isValid: false, message: VALIDATION_MESSAGES.required };
        if (password !== confirmPassword) {
            return { isValid: false, message: VALIDATION_MESSAGES.confirmPassword };
        }
        return { isValid: true, message: '' };
    },
    
    // Generic field validation
    validateRequired: (value, fieldName) => {
        if (!value || value.trim() === '') {
            return { isValid: false, message: ${fieldName} is required };
        }
        return { isValid: true, message: '' };
    }
};

// Real-time validation helper
function addRealTimeValidation(inputElement, validationFunction, errorElementId) {
    inputElement.addEventListener('input', function() {
        const result = validationFunction(this.value);
        const errorElement = document.getElementById(errorElementId);
        
        if (!result.isValid) {
            this.classList.add('invalid');
            this.classList.remove('valid');
            if (errorElement) {
                errorElement.textContent = result.message;
                errorElement.style.display = 'block';
            }
        } else {
            this.classList.add('valid');
            this.classList.remove('invalid');
            if (errorElement) {
                errorElement.textContent = '';
                errorElement.style.display = 'none';
            }
        }
    });
}

// Export for use in other files (if using modules)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { Validator, VALIDATION_PATTERNS, VALIDATION_MESSAGES, addRealTimeValidation };
}
