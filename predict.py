"""
Prediction Module for Student Performance
Provides interface for making predictions with trained models
"""

import joblib
import pandas as pd
import numpy as np
import sys
import json
import os
import warnings
warnings.filterwarnings('ignore')

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Load the model and preprocessors
try:
    # Try different possible paths
    model_paths = [
        os.path.join(SCRIPT_DIR, 'model.pkl'),
        os.path.join(SCRIPT_DIR, 'models', 'model.pkl'),
        'model.pkl'
    ]
    
    encoder_paths = [
        os.path.join(SCRIPT_DIR, 'label_encoder.pkl'),
        os.path.join(SCRIPT_DIR, 'models', 'label_encoder.pkl'),
        'label_encoder.pkl'
    ]
    
    scaler_paths = [
        os.path.join(SCRIPT_DIR, 'scaler.pkl'),
        os.path.join(SCRIPT_DIR, 'models', 'scaler.pkl'),
        'scaler.pkl'
    ]
    
    features_paths = [
        os.path.join(SCRIPT_DIR, 'feature_columns.pkl'),
        os.path.join(SCRIPT_DIR, 'models', 'feature_columns.pkl'),
        'feature_columns.pkl'
    ]
    
    # Load model
    model = None
    for path in model_paths:
        if os.path.exists(path):
            model = joblib.load(path)
            print(f"✅ Model loaded from {path}", file=sys.stderr)
            break
    
    # Load encoder
    label_encoder = None
    for path in encoder_paths:
        if os.path.exists(path):
            label_encoder = joblib.load(path)
            print(f"✅ Encoder loaded from {path}", file=sys.stderr)
            break
    
    # Load scaler
    scaler = None
    for path in scaler_paths:
        if os.path.exists(path):
            scaler = joblib.load(path)
            print(f"✅ Scaler loaded from {path}", file=sys.stderr)
            break
    
    # Load features
    feature_columns = None
    for path in features_paths:
        if os.path.exists(path):
            feature_columns = joblib.load(path)
            print(f"✅ Features loaded from {path}", file=sys.stderr)
            break
    
    if model is None or label_encoder is None:
        print("ERROR: Could not load model files", file=sys.stderr)
        sys.exit(1)
        
    # Print expected features
    if feature_columns is not None:
        print(f"✅ Model expects {len(feature_columns)} features: {feature_columns}", file=sys.stderr)
        
except Exception as e:
    print(f"ERROR loading model: {str(e)}", file=sys.stderr)
    sys.exit(1)

def predict_performance(attendance, assignments, engagement, study_hours, previous_grade, extra_curricular, parent_education):
    """
    Predict student performance based on ALL 7 features
    """
    try:
        # Create a dictionary with ALL 7 features
        input_dict = {
            'attendance': attendance,
            'assignments': assignments,
            'engagement': engagement,
            'study_hours': study_hours,
            'previous_grade': previous_grade,
            'extra_curricular': extra_curricular,
            'parent_education': parent_education
        }
        
        # Determine which features to use based on what the model expects
        if feature_columns is not None:
            # Use the exact features the model expects
            feature_dict = {col: input_dict.get(col, 0) for col in feature_columns}
            input_data = pd.DataFrame([feature_dict])
            print(f"✅ Using {len(feature_columns)} features: {list(feature_dict.keys())}", file=sys.stderr)
            print(f"   Values: {feature_dict}", file=sys.stderr)
        else:
            # Fallback to basic 3 features
            input_data = pd.DataFrame([[attendance, assignments, engagement]], 
                                     columns=['attendance', 'assignments', 'engagement'])
            print(f"⚠️ Using basic 3 features (attendance, assignments, engagement)", file=sys.stderr)
        
        # Scale if scaler is available
        if scaler is not None:
            input_scaled = scaler.transform(input_data)
            print(f"✅ Data scaled successfully", file=sys.stderr)
        else:
            input_scaled = input_data
            print(f"⚠️ No scaler available, using raw data", file=sys.stderr)
        
        # Make prediction
        prediction_encoded = model.predict(input_scaled)[0]
        
        # Convert prediction to class name
        if hasattr(label_encoder, 'inverse_transform'):
            prediction_class = label_encoder.inverse_transform([prediction_encoded])[0]
        else:
            prediction_class = prediction_encoded
        
        # Get probabilities if available
        confidence = 0
        prob_dict = {}
        
        if hasattr(model, 'predict_proba'):
            probabilities = model.predict_proba(input_scaled)[0]
            confidence = np.max(probabilities) * 100
            
            # Create probability dictionary
            if hasattr(label_encoder, 'classes_'):
                for i, cls in enumerate(label_encoder.classes_):
                    prob_dict[cls] = float(probabilities[i])
            else:
                classes = ['Poor', 'Average', 'Good', 'Excellent']
                for i, cls in enumerate(classes[:len(probabilities)]):
                    prob_dict[cls] = float(probabilities[i])
        else:
            confidence = 100.0
        
        print(f"✅ Prediction: {prediction_class} (Confidence: {confidence:.1f}%)", file=sys.stderr)
        
        return prediction_class, confidence, prob_dict
        
    except Exception as e:
        print(f"ERROR in prediction: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        raise

def validate_input(value, name, min_val=0, max_val=100):
    """Validate input value"""
    try:
        val = float(value)
        if val < min_val or val > max_val:
            raise ValueError(f"{name} must be between {min_val} and {max_val}")
        return val
    except ValueError as e:
        raise ValueError(f"Invalid {name}: {str(e)}")

if __name__ == "__main__":
    # Read input from command line
    if len(sys.argv) > 1:
        try:
            # Parse input data
            data = json.loads(sys.argv[1])
            
            print(f"Received data: {data}", file=sys.stderr)
            
            # Validate ALL 7 inputs
            attendance = validate_input(data['attendance'], 'attendance', 0, 100)
            assignments = validate_input(data['assignments'], 'assignments', 0, 100)
            engagement = validate_input(data['engagement'], 'engagement', 0, 100)
            study_hours = validate_input(data['study_hours'], 'study_hours', 0, 40)
            previous_grade = validate_input(data['previous_grade'], 'previous_grade', 0, 100)
            extra_curricular = validate_input(data['extra_curricular'], 'extra_curricular', 0, 10)
            parent_education = validate_input(data['parent_education'], 'parent_education', 1, 4)
            
            # Print debug info
            print(f"DEBUG - Input percentages: Attendance={attendance}%, Assignments={assignments}%, Engagement={engagement}%", file=sys.stderr)
            print(f"DEBUG - Additional features: Study Hours={study_hours}, Previous Grade={previous_grade}%, Extra Curricular={extra_curricular}, Parent Education={parent_education}", file=sys.stderr)
            
            # Make prediction with ALL 7 features
            prediction, confidence, probabilities = predict_performance(
                attendance, 
                assignments, 
                engagement,
                study_hours,
                previous_grade,
                extra_curricular,
                parent_education
            )
            
            # Print debug info
            print(f"DEBUG - Confidence: {confidence:.1f}%", file=sys.stderr)
            print(f"DEBUG - Class probabilities: {probabilities}", file=sys.stderr)
            
            # Return result as JSON
            result = {
                'success': True,
                'prediction': prediction,
                'confidence': confidence,
                'probabilities': probabilities
            }
            print(json.dumps(result))
            
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
            print(json.dumps({'success': False, 'error': 'Invalid JSON input'}))
        except ValueError as e:
            print(f"Error: {str(e)}", file=sys.stderr)
            print(json.dumps({'success': False, 'error': str(e)}))
        except Exception as e:
            print(f"Unexpected error: {str(e)}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            print(json.dumps({'success': False, 'error': str(e)}))
    else:
        # Test mode - run test cases
        print("\n🧪 Running prediction tests...\n", file=sys.stderr)
        
        test_cases = [
            {
                "name": "Excellent Student",
                "attendance": 95, "assignments": 95, "engagement": 95,
                "study_hours": 20, "previous_grade": 90, "extra_curricular": 3, "parent_education": 4
            },
            {
                "name": "Good Student",
                "attendance": 85, "assignments": 80, "engagement": 85,
                "study_hours": 15, "previous_grade": 80, "extra_curricular": 2, "parent_education": 3
            },
            {
                "name": "Average Student",
                "attendance": 65, "assignments": 60, "engagement": 70,
                "study_hours": 10, "previous_grade": 65, "extra_curricular": 2, "parent_education": 2
            },
            {
                "name": "Poor Student",
                "attendance": 40, "assignments": 35, "engagement": 30,
                "study_hours": 5, "previous_grade": 45, "extra_curricular": 0, "parent_education": 1
            },
        ]
        
        for test in test_cases:
            try:
                pred, conf, probs = predict_performance(
                    test["attendance"], 
                    test["assignments"], 
                    test["engagement"],
                    test["study_hours"],
                    test["previous_grade"],
                    test["extra_curricular"],
                    test["parent_education"]
                )
                
                print(f"📌 {test['name']}: {pred} ({conf:.1f}%)", file=sys.stderr)
                print(f"   Probabilities: {probs}", file=sys.stderr)
                print(file=sys.stderr)
            except Exception as e:
                print(f"❌ {test['name']}: Error - {str(e)}", file=sys.stderr)
 