# This is a placeholder model file
# In production, you would train and save your actual Random Forest model here

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier

# Create a simple model for demonstration
def create_demo_model():
    # Simple training data
    X = np.array([
        [4.0, 8, 5, 4.0],  # A, 8hrs, high confidence, high difficulty
        [3.0, 5, 3, 3.0],  # B, 5hrs, medium, medium
        [2.0, 2, 2, 4.0],  # C, 2hrs, low, high
        [1.0, 1, 1, 5.0],  # D, 1hr, very low, very high
    ])
    y = np.array(['A', 'B', 'C', 'D'])
    
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X, y)
    
    return model

# Save model
model = create_demo_model()
joblib.dump(model, 'model.pkl')
print("Demo model created and saved as model.pkl")
