from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import pandas as pd
import numpy as np
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all origins

# Load model and preprocessors
print("Loading model...")
try:
    model = joblib.load('model.pkl')
    label_encoder = joblib.load('label_encoder.pkl')
    scaler = joblib.load('scaler.pkl')
    feature_columns = joblib.load('feature_columns.pkl')
    print("✅ Model loaded successfully!")
    print(f"   Features: {feature_columns}")
    print(f"   Classes: {label_encoder.classes_}")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    raise

@app.route('/')
def home():
    return jsonify({
        'name': 'Student Performance Predictor API',
        'status': 'running',
        'version': '2.0',
        'endpoints': {
            'predict': 'POST /predict',
            'health': 'GET /health'
        }
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'timestamp': pd.Timestamp.now().isoformat(),
        'message': 'Server is running',
        'model_loaded': True
    })

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        logger.info(f"Prediction request received")
        
        # Extract all 7 features with validation
        try:
            attendance = float(data.get('attendance', 0))
            assignments = float(data.get('assignments', 0))
            engagement = float(data.get('engagement', 0))
            study_hours = float(data.get('study_hours', 10))
            previous_grade = float(data.get('previous_grade', 65))
            extra_curricular = float(data.get('extra_curricular', 2))
            parent_education = float(data.get('parent_education', 2))
        except ValueError as e:
            return jsonify({'success': False, 'error': f'Invalid numeric value: {str(e)}'}), 400
        
        # Validate ranges
        if not (0 <= attendance <= 100):
            return jsonify({'success': False, 'error': 'Attendance must be between 0 and 100'}), 400
        if not (0 <= assignments <= 100):
            return jsonify({'success': False, 'error': 'Assignments must be between 0 and 100'}), 400
        if not (0 <= engagement <= 100):
            return jsonify({'success': False, 'error': 'Engagement must be between 0 and 100'}), 400
        if not (0 <= study_hours <= 40):
            return jsonify({'success': False, 'error': 'Study hours must be between 0 and 40'}), 400
        if not (0 <= previous_grade <= 100):
            return jsonify({'success': False, 'error': 'Previous grade must be between 0 and 100'}), 400
        if not (0 <= extra_curricular <= 5):
            return jsonify({'success': False, 'error': 'Extra curricular must be between 0 and 5'}), 400
        if not (1 <= parent_education <= 4):
            return jsonify({'success': False, 'error': 'Parent education must be between 1 and 4'}), 400
        
        # Create input dataframe
        input_dict = {
            'attendance': attendance,
            'assignments': assignments,
            'engagement': engagement,
            'study_hours': study_hours,
            'previous_grade': previous_grade,
            'extra_curricular': extra_curricular,
            'parent_education': parent_education
        }
        
        # Use feature columns in correct order
        input_data = pd.DataFrame([[input_dict[col] for col in feature_columns]], columns=feature_columns)
        
        # Scale input
        input_scaled = scaler.transform(input_data)
        
        # Make prediction
        prediction_encoded = model.predict(input_scaled)[0]
        prediction_class = label_encoder.inverse_transform([prediction_encoded])[0]
        
        # Get probabilities
        probabilities = model.predict_proba(input_scaled)[0]
        confidence = np.max(probabilities) * 100
        
        # Calculate weighted average for grade
        weighted_avg = (attendance * 0.20 + assignments * 0.20 + engagement * 0.15 + 
                       study_hours * 0.15 + previous_grade * 0.15 + 
                       extra_curricular * 0.10 + parent_education * 0.05)
        
        result = {
            'success': True,
            'prediction': prediction_class,
            'confidence': float(confidence),
            'weighted_score': float(weighted_avg),
            'probabilities': {cls: float(prob) for cls, prob in zip(label_encoder.classes_, probabilities)}
        }
        
        logger.info(f"Prediction result: {prediction_class} ({confidence:.1f}%)")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in prediction: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)