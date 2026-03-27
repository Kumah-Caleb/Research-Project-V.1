import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import joblib
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("STUDENT PERFORMANCE ML MODEL TRAINING")
print("=" * 60)

# Load data
df = pd.read_csv('student_data.csv')
print(f"Loaded {len(df)} records")

# Define features and target
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
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded)

print(f"Training set: {len(X_train)} samples")
print(f"Test set: {len(X_test)} samples")

# Train Random Forest model
print("\nTraining Random Forest Classifier...")
rf_model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
rf_model.fit(X_train, y_train)

# Evaluate
y_pred = rf_model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"Random Forest Accuracy: {accuracy:.3f}")

print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=label_encoder.classes_))

# Feature importance
feature_importance = pd.DataFrame({
    'feature': feature_columns,
    'importance': rf_model.feature_importances_
}).sort_values('importance', ascending=False)

print("\nFeature Importance:")
for _, row in feature_importance.iterrows():
    print(f"  {row['feature']}: {row['importance']:.3f}")

# Save model and preprocessors
joblib.dump(rf_model, 'model.pkl')
joblib.dump(label_encoder, 'label_encoder.pkl')
joblib.dump(scaler, 'scaler.pkl')
joblib.dump(feature_columns, 'feature_columns.pkl')

print("\n✅ Model saved successfully!")
print("Files created:")
print("  - model.pkl (Random Forest Classifier)")
print("  - label_encoder.pkl")
print("  - scaler.pkl")
print("  - feature_columns.pkl")

# Test predictions
print("\n🧪 Testing model with sample inputs:")
test_cases = [
    [95, 95, 95, 18, 90, 4, 4],
    [85, 80, 85, 14, 80, 3, 3],
    [65, 60, 70, 10, 65, 2, 2],
    [40, 35, 30, 5, 40, 1, 1],
]

for test in test_cases:
    test_input = np.array(test).reshape(1, -1)
    test_scaled = scaler.transform(test_input)
    pred = rf_model.predict(test_scaled)[0]
    pred_class = label_encoder.inverse_transform([pred])[0]
    proba = rf_model.predict_proba(test_scaled)[0]
    confidence = np.max(proba) * 100
    print(f"  Input: {test[:3]}... → Prediction: {pred_class} ({confidence:.1f}%)")

print("\n✨ Training complete!")
