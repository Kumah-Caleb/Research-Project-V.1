from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import pandas as pd
import numpy as np
import os

app = Flask(__name__)
CORS(app)

# Load model and preprocessors
print("Loading model...")
try:
    model = joblib.load('model.pkl')
    label_encoder = joblib.load('label_encoder.pkl')
    scaler = joblib.load('scaler.pkl')
    feature_columns = joblib.load('feature_columns.pkl')
    print("✅ Model loaded successfully!")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    model = None

@app.route('/')
def home():
    return jsonify({
        'name': 'Student Performance Predictor API',
        'status': 'running',
        'endpoints': {
            'predict': 'POST /predict',
            'health': 'GET /health'
        }
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'model_loaded': model is not None,
        'message': 'Server is running'
    })

@app.route('/predict', methods=['POST'])
def predict():
    try:
        if model is None:
            return jsonify({'success': False, 'error': 'Model not loaded'}), 503
            
        data = request.json
        attendance = float(data.get('attendance', 0))
        assignments = float(data.get('assignments', 0))
        engagement = float(data.get('engagement', 0))
        study_hours = float(data.get('study_hours', 10))
        previous_grade = float(data.get('previous_grade', 65))
        extra_curricular = float(data.get('extra_curricular', 2))
        parent_education = float(data.get('parent_education', 2))
        
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
        
        return jsonify({
            'success': True,
            'prediction': prediction_class,
            'confidence': float(confidence),
            'weighted_score': float(weighted_avg)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
