from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import numpy as np
import pandas as pd
import joblib

app = Flask(__name__)
CORS(app)

# Global variables for ML model
model = None
label_encoder = None
scaler = None
feature_columns = None

# Try to load ML model if available
def load_ml_model():
    global model, label_encoder, scaler, feature_columns
    try:
        if os.path.exists('model.pkl'):
            model = joblib.load('model.pkl')
            label_encoder = joblib.load('label_encoder.pkl')
            scaler = joblib.load('scaler.pkl')
            feature_columns = joblib.load('feature_columns.pkl')
            print("✅ ML Model loaded successfully!")
            return True
        else:
            print("⚠️ ML model files not found, using rule-based fallback")
            return False
    except Exception as e:
        print(f"❌ Error loading ML model: {e}")
        return False

# Load model on startup
ML_AVAILABLE = load_ml_model()

def rule_based_prediction(data):
    """Fallback rule-based prediction when ML model is unavailable"""
    attendance = data.get('attendance', 0)
    assignments = data.get('assignments', 0)
    engagement = data.get('engagement', 0)
    study_hours = data.get('study_hours', 0)
    previous_grade = data.get('previous_grade', 0)
    extra_curricular = data.get('extra_curricular', 0)
    parent_education = data.get('parent_education', 2)
    
    # Weighted score calculation
    weighted_score = (
        attendance * 0.25 +
        assignments * 0.25 +
        engagement * 0.15 +
        (study_hours / 20 * 100) * 0.15 +
        previous_grade * 0.10 +
        (extra_curricular / 5 * 100) * 0.05 +
        (parent_education / 4 * 100) * 0.05
    )
    
    # Determine prediction
    if weighted_score >= 85:
        prediction = "Excellent"
    elif weighted_score >= 70:
        prediction = "Good"
    elif weighted_score >= 50:
        prediction = "Average"
    else:
        prediction = "Poor"
    
    # Calculate confidence (simple rule-based)
    confidence = min(95, max(60, weighted_score))
    
    return {
        'success': True,
        'prediction': prediction,
        'confidence': float(confidence),
        'weighted_score': float(weighted_score),
        'model_used': 'rule-based'
    }

def ml_prediction(data):
    """Use ML model for prediction"""
    try:
        attendance = data.get('attendance', 0)
        assignments = data.get('assignments', 0)
        engagement = data.get('engagement', 0)
        study_hours = data.get('study_hours', 10)
        previous_grade = data.get('previous_grade', 65)
        extra_curricular = data.get('extra_curricular', 2)
        parent_education = data.get('parent_education', 2)
        
        input_dict = {
            'attendance': attendance,
            'assignments': assignments,
            'engagement': engagement,
            'study_hours': study_hours,
            'previous_grade': previous_grade,
            'extra_curricular': extra_curricular,
            'parent_education': parent_education
        }
        
        input_data = pd.DataFrame([[input_dict[col] for col in feature_columns]], columns=feature_columns)
        input_scaled = scaler.transform(input_data)
        prediction_encoded = model.predict(input_scaled)[0]
        prediction_class = label_encoder.inverse_transform([prediction_encoded])[0]
        
        probabilities = model.predict_proba(input_scaled)[0]
        confidence = np.max(probabilities) * 100
        
        weighted_avg = (attendance * 0.20 + assignments * 0.20 + engagement * 0.15 + 
                       study_hours * 0.15 + previous_grade * 0.15 + 
                       extra_curricular * 0.10 + parent_education * 0.05)
        
        return {
            'success': True,
            'prediction': str(prediction_class),
            'confidence': float(confidence),
            'weighted_score': float(weighted_avg),
            'model_used': 'ml'
        }
    except Exception as e:
        print(f"ML prediction error: {e}, falling back to rule-based")
        return rule_based_prediction(data)

@app.route('/')
def home():
    return jsonify({
        'name': 'Student Performance Predictor API',
        'status': 'running',
        'version': '2.0',
        'model_available': ML_AVAILABLE,
        'endpoints': {
            'predict': 'POST /predict',
            'health': 'GET /health',
            'info': 'GET /info'
        }
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'model_available': ML_AVAILABLE,
        'message': 'Server is running'
    })

@app.route('/info', methods=['GET'])
def info():
    return jsonify({
        'name': 'Student Performance Predictor',
        'version': '2.0',
        'model': 'ML Model' if ML_AVAILABLE else 'Rule-based Fallback',
        'features': ['attendance', 'assignments', 'engagement', 'study_hours', 
                    'previous_grade', 'extra_curricular', 'parent_education'],
        'outputs': ['Excellent', 'Good', 'Average', 'Poor']
    })

@app.route('/predict', methods=['POST', 'OPTIONS'])
def predict():
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Validate inputs
        required_fields = ['attendance', 'assignments', 'engagement']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Validate ranges
        validations = [
            (data.get('attendance', 0), 0, 100, 'Attendance'),
            (data.get('assignments', 0), 0, 100, 'Assignments'),
            (data.get('engagement', 0), 0, 100, 'Engagement'),
            (data.get('study_hours', 10), 0, 40, 'Study hours'),
            (data.get('previous_grade', 65), 0, 100, 'Previous grade'),
            (data.get('extra_curricular', 2), 0, 5, 'Extra curricular'),
            (data.get('parent_education', 2), 1, 4, 'Parent education')
        ]
        
        for val, min_val, max_val, name in validations:
            if not (min_val <= val <= max_val):
                return jsonify({'success': False, 'error': f'{name} must be between {min_val} and {max_val}'}), 400
        
        # Use ML if available, otherwise fallback to rule-based
        if ML_AVAILABLE:
            result = ml_prediction(data)
        else:
            result = rule_based_prediction(data)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"Starting server on port {port}")
    print(f"ML Model Available: {ML_AVAILABLE}")
    app.run(host='0.0.0.0', port=port, debug=False)