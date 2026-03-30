// config.js - Configuration for USTED Predictor

const APP_CONFIG = {
    // University name
    universityName: 'USTED',
    
    // API endpoints
    apiBaseUrl: 'https://aamusted-predictor-backend2.onrender.com',
    
    // App version
    version: '1.0.0',
    
    // Validation patterns
    validationPatterns: {
        studentId: /^[A-Z]{3}\d{5,7}$/,
        courseCode: /^[A-Z]{2,4}\d{3,4}$/,
        email: /^[a-zA-Z0-9._%+-]+@(usted\.edu\.gh|[a-z]+\.usted\.edu\.gh)$/,
        password: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,}$/
    }
};

// Update page titles
document.addEventListener('DOMContentLoaded', function() {
    if (document.title.includes('AAMUSTED')) {
        document.title = document.title.replace('AAMUSTED', APP_CONFIG.universityName);
    }
});

// Export for use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = APP_CONFIG;
}
