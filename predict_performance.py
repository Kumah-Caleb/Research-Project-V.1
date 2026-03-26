import pickle
import sys

def test_prediction():
    try:
        # Load the model
        with open('model.pkl', 'rb') as f:
            model = pickle.load(f)
        
        print("Model loaded successfully!")
        print(f"Model type: {type(model)}")
        print(f"Expected features: attendance, assignments, engagement")
        print(f"Possible outcomes: {model.classes_}")
        print("\nTesting with sample data...")
        
        # Test multiple predictions
        test_cases = [
            [85, 80, 90],   # Should be Good
            [95, 95, 98],   # Should be Excellent
            [60, 50, 65],   # Should be Poor
            [75, 70, 80],   # Should be Average
        ]
        
        for test in test_cases:
            prediction = model.predict([test])
            print(f"Input (attendance={test[0]}, assignments={test[1]}, engagement={test[2]})")
            print(f"Predicted performance: {prediction[0]}\n")
            
    except FileNotFoundError:
        print("Error: model.pkl not found. Please run train_model.py first.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Check if command line arguments provided
    if len(sys.argv) == 4:
        try:
            attendance = float(sys.argv[1])
            assignments = float(sys.argv[2])
            engagement = float(sys.argv[3])
            
            with open('model.pkl', 'rb') as f:
                model = pickle.load(f)
            
            prediction = model.predict([[attendance, assignments, engagement]])
            print(f"Predicted performance: {prediction[0]}")
        except Exception as e:
            print(f"Error making prediction: {e}")
    else:
        test_prediction()