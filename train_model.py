import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, accuracy_score
import joblib
import os

print("=" * 60)
print("Training Student Performance Prediction Model")
print("=" * 60)

# Generate enhanced synthetic data
np.random.seed(42)
n_samples = 1000

# Generate features
attendance = np.random.randint(30, 100, n_samples)
assignments = np.random.randint(30, 100, n_samples)
engagement = np.random.randint(30, 100, n_samples)
study_hours = np.random.randint(0, 21, n_samples)
previous_grade = np.random.randint(30, 100, n_samples)
extra_curricular = np.random.choice([0, 1, 2, 3, 4, 5], n_samples, p=[0.1, 0.2, 0.3, 0.2, 0.15, 0.05])
parent_education = np.random.choice([1, 2, 3, 4], n_samples, p=[0.3, 0.4, 0.2, 0.1])

# Generate target based on weighted score
def determine_performance(att, ass, eng, study, prev, extra, parent):
    weighted_score = (
        att * 0.25 + ass * 0.25 + eng * 0.15 +
        (study / 20 * 100) * 0.15 + prev * 0.10 +
        (extra / 5 * 100) * 0.05 + (parent / 4 * 100) * 0.05
    )
    if weighted_score >= 85:
        return 'Excellent'
    elif weighted_score >= 70:
        return 'Good'
    elif weighted_score >= 50:
        return 'Average'
    else:
        return 'Poor'

performance = [determine_performance(att, ass, eng, study, prev, extra, parent) 
               for att, ass, eng, study, prev, extra, parent in 
               zip(attendance, assignments, engagement, study_hours, 
                   previous_grade, extra_curricular, parent_education)]

# Create DataFrame
df = pd.DataFrame({
    'attendance': attendance,
    'assignments': assignments,
    'engagement': engagement,
    'study_hours': study_hours,
    'previous_grade': previous_grade,
    'extra_curricular': extra_curricular,
    'parent_education': parent_education,
    'performance': performance
})

print(f"Generated {len(df)} samples")
print(f"Features: {df.columns.tolist()}")

# Prepare features and target
feature_columns = ['attendance', 'assignments', 'engagement', 'study_hours', 
                   'previous_grade', 'extra_curricular', 'parent_education']
X = df[feature_columns]
y = df['performance']

# Encode target
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

# Scale features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Split data
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y_encoded, test_size=0.2, random_state=42)

# Train model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"\nModel Accuracy: {accuracy:.3f}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=label_encoder.classes_))

# Save model and preprocessors
joblib.dump(model, 'model.pkl')
joblib.dump(label_encoder, 'label_encoder.pkl')
joblib.dump(scaler, 'scaler.pkl')
joblib.dump(feature_columns, 'feature_columns.pkl')

print("\n✅ Model saved successfully!")
print(f"Files created: model.pkl, label_encoder.pkl, scaler.pkl, feature_columns.pkl")