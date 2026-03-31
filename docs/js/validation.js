// validation.js - Complete form validation for USTED

const VALIDATION_PATTERNS = {
    email: /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/,
    password: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,}$/,
    studentId: /^[A-Z]{3}\d{5,7}$/,
    name: /^[a-zA-Z\s\-']{2,50}$/,
    courseCode: /^[A-Z]{2,4}\d{3,4}$/
};

function validateEmail(email) {
    if (!email) return { isValid: false, message: 'Email is required' };
    if (!VALIDATION_PATTERNS.email.test(email)) {
        return { isValid: false, message: 'Please enter a valid email address (e.g., student@example.com)' };
    }
    return { isValid: true, message: '' };
}

function validatePassword(password) {
    if (!password) return { isValid: false, message: 'Password is required' };
    if (!VALIDATION_PATTERNS.password.test(password)) {
        return { isValid: false, message: 'Password must be at least 8 characters with 1 uppercase, 1 lowercase, and 1 number' };
    }
    return { isValid: true, message: '' };
}

function validateStudentId(studentId) {
    if (!studentId) return { isValid: false, message: 'Student ID is required' };
    if (!VALIDATION_PATTERNS.studentId.test(studentId.toUpperCase())) {
        return { isValid: false, message: 'Student ID must be 3 uppercase letters followed by 5-7 digits (e.g., ITE12345)' };
    }
    return { isValid: true, message: '' };
}

function validateName(name) {
    if (!name) return { isValid: false, message: 'Name is required' };
    if (!VALIDATION_PATTERNS.name.test(name)) {
        return { isValid: false, message: 'Name must be 2-50 characters (letters, spaces, hyphens, apostrophes only)' };
    }
    return { isValid: true, message: '' };
}

function validateCourseCode(courseCode) {
    if (!courseCode) return { isValid: false, message: 'Course code is required' };
    if (!VALIDATION_PATTERNS.courseCode.test(courseCode.toUpperCase())) {
        return { isValid: false, message: 'Course code must be 2-4 uppercase letters followed by 3-4 digits (e.g., ITE301, CS101)' };
    }
    return { isValid: true, message: '' };
}
