from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import numpy as np

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({
        'name': 'Student Performance Predictor API',
        'status': 'running',
        'version': '1.0',
        'endpoints': {
            'predict': 'POST /predict',
            'health': 'GET /health'
        }
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'message': 'Server is running',
        'model': 'rule-based (fallback)'
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
        
        # Extract features
        attendance = float(data.get('attendance', 0))
        assignments = float(data.get('assignments', 0))
        engagement = float(data.get('engagement', 0))
        study_hours = float(data.get('study_hours', 0))
        previous_grade = float(data.get('previous_grade', 0))
        extra_curricular = float(data.get('extra_curricular', 0))
        parent_education = float(data.get('parent_education', 2))
        
        # Simple weighted score calculation
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
        
        result = {
            'success': True,
            'prediction': prediction,
            'confidence': float(confidence),
            'weighted_score': float(weighted_score)
        }
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port)
