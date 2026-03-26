import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import joblib
import warnings
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os

warnings.filterwarnings('ignore')

print("=" * 60)
print("STUDENT PERFORMANCE PREDICTION MODEL TRAINING")
print("=" * 60)
print(f"Training started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

# Create output directory for visualizations
os.makedirs('visualizations', exist_ok=True)

# Try to load existing data, if not found generate synthetic data
try:
    df = pd.read_csv('student_performance.csv')
    print(f"\n✅ Loaded {len(df)} records from CSV")
    
    # Check which columns we have
    existing_columns = df.columns.tolist()
    print(f"📋 Existing columns: {existing_columns}")
    
    # If we don't have all the new features, add them
    required_features = ['attendance', 'assignments', 'engagement']
    additional_features = ['study_hours', 'previous_grade', 'extra_curricular', 'parent_education']
    
    missing_features = [f for f in additional_features if f not in existing_columns]
    
    if missing_features:
        print(f"\n⚠️ Missing features detected: {missing_features}")
        print("Adding synthetic data for missing features...")
        
        # Add missing features based on existing data
        np.random.seed(42)
        
        for feature in missing_features:
            if feature == 'study_hours':
                # Generate study hours correlated with attendance
                df['study_hours'] = df['attendance'].apply(
                    lambda x: np.random.randint(
                        max(0, int(x/10) - 2),
                        min(20, int(x/10) + 5)
                    )
                )
            elif feature == 'previous_grade':
                # Generate previous grade correlated with current performance
                df['previous_grade'] = df.apply(
                    lambda row: np.random.randint(
                        max(20, row['attendance'] - 15),
                        min(100, row['attendance'] + 10)
                    ), axis=1
                )
            elif feature == 'extra_curricular':
                # Generate extra curricular activities (0-5)
                df['extra_curricular'] = df['engagement'].apply(
                    lambda x: np.random.choice([0, 1, 2, 3, 4, 5],
                                              p=[0.1, 0.2, 0.3, 0.2, 0.15, 0.05])
                )
            elif feature == 'parent_education':
                # Generate parent education level (1-4)
                df['parent_education'] = np.random.choice([1, 2, 3, 4], 
                                                          size=len(df),
                                                          p=[0.3, 0.4, 0.2, 0.1])
            
            print(f"  ✅ Added {feature}")
        
        # Save the enhanced dataset
        df.to_csv('student_performance_enhanced.csv', index=False)
        print("\n✅ Enhanced dataset saved as 'student_performance_enhanced.csv'")
        
except FileNotFoundError:
    print("\n⚠️ No existing data found. Generating enhanced synthetic data...")
    
    # Generate synthetic data with realistic patterns
    np.random.seed(42)
    n_samples = 500  # Increased to 500 samples for better training
    
    # Generate features with realistic correlations
    attendance = np.random.randint(30, 100, n_samples)
    
    # Additional features
    study_hours = []
    previous_grade = []
    extra_curricular = []
    parent_education = []
    assignments = []
    engagement = []
    
    for att in attendance:
        # Study hours (0-20 hours per week)
        if att >= 85:
            study_hours.append(np.random.randint(15, 21))
        elif att >= 70:
            study_hours.append(np.random.randint(10, 18))
        elif att >= 50:
            study_hours.append(np.random.randint(5, 15))
        else:
            study_hours.append(np.random.randint(0, 10))
        
        # Previous grade (0-100)
        if att >= 85:
            previous_grade.append(np.random.randint(80, 101))
        elif att >= 70:
            previous_grade.append(np.random.randint(65, 90))
        elif att >= 50:
            previous_grade.append(np.random.randint(45, 75))
        else:
            previous_grade.append(np.random.randint(20, 55))
        
        # Extra curricular (0-5 activities)
        extra_curricular.append(np.random.choice([0, 1, 2, 3, 4, 5], 
                                               p=[0.1, 0.2, 0.3, 0.2, 0.15, 0.05]))
        
        # Parent education level (1-4: High School, Bachelor, Master, PhD)
        parent_education.append(np.random.choice([1, 2, 3, 4], 
                                               p=[0.3, 0.4, 0.2, 0.1]))
        
        # Assignments and engagement with correlation to attendance
        if att >= 85:
            assignments.append(np.random.randint(75, 100))
            engagement.append(np.random.randint(70, 100))
        elif att >= 70:
            assignments.append(np.random.randint(60, 90))
            engagement.append(np.random.randint(55, 90))
        elif att >= 50:
            assignments.append(np.random.randint(40, 75))
            engagement.append(np.random.randint(35, 70))
        else:
            assignments.append(np.random.randint(20, 55))
            engagement.append(np.random.randint(15, 50))
    
    # Create target based on multiple factors
    def determine_performance(att, ass, eng, study, prev_grade, extra, parent_edu):
        # Weighted score with multiple factors
        weighted_score = (
            att * 0.25 +           # Attendance (25%)
            ass * 0.20 +           # Assignments (20%)
            eng * 0.15 +           # Engagement (15%)
            (study / 20 * 100) * 0.15 +  # Study hours (15%)
            prev_grade * 0.15 +    # Previous grade (15%)
            (extra / 5 * 100) * 0.05 +   # Extra curricular (5%)
            (parent_edu / 4 * 100) * 0.05  # Parent education (5%)
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
    
    # Create DataFrame with all features
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
    
    # Save to CSV
    df.to_csv('student_performance.csv', index=False)
    print(f"✅ Generated {n_samples} enhanced synthetic records and saved to 'student_performance.csv'")

# Define feature columns (use only available columns)
base_features = ['attendance', 'assignments', 'engagement']
optional_features = ['study_hours', 'previous_grade', 'extra_curricular', 'parent_education']

# Use only features that exist in the dataframe
feature_columns = [f for f in base_features + optional_features if f in df.columns]
print(f"\n📊 Using features: {feature_columns}")

# Display basic statistics
print(f"\n📊 Dataset Overview:")
print(f"  Total samples: {len(df)}")
print(f"  Features: {len(feature_columns)}")
print(f"  Target classes: {df['performance'].nunique()}")

# Display sample data
print("\n📋 Sample data (first 5 rows):")
print(df[feature_columns + ['performance']].head())

# Display feature ranges
print("\n📊 Feature Statistics:")
for col in feature_columns:
    print(f"  {col.replace('_', ' ').title()}:")
    print(f"    Range: {df[col].min()} - {df[col].max()}")
    print(f"    Mean: {df[col].mean():.1f}")
    print(f"    Std: {df[col].std():.1f}")

# Display performance distribution
print("\n📈 Performance Distribution:")
performance_dist = df['performance'].value_counts()
for perf, count in performance_dist.items():
    percentage = (count / len(df)) * 100
    print(f"  {perf}: {count} ({percentage:.1f}%)")

# Visualize performance distribution
plt.figure(figsize=(10, 6))
sns.countplot(data=df, x='performance', order=['Poor', 'Average', 'Good', 'Excellent'])
plt.title('Student Performance Distribution')
plt.xlabel('Performance Category')
plt.ylabel('Count')
plt.tight_layout()
plt.savefig('visualizations/performance_distribution.png')
plt.close()

# Visualize feature correlations
plt.figure(figsize=(12, 8))
# Select only numeric columns for correlation
numeric_cols = df[feature_columns].select_dtypes(include=[np.number]).columns
if len(numeric_cols) > 1:
    correlation_matrix = df[numeric_cols].corr()
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0, fmt='.2f')
    plt.title('Feature Correlation Matrix')
    plt.tight_layout()
    plt.savefig('visualizations/correlation_matrix.png')
    plt.close()
    print("\n📊 Correlation matrix saved to 'visualizations/correlation_matrix.png'")

# Prepare features and target
X = df[feature_columns]
y = df['performance']

# Encode target labels
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

# Scale features for models that benefit from scaling
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Split the data
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
)

print(f"\n🎯 Training set size: {len(X_train)} samples")
print(f"🎯 Test set size: {len(X_test)} samples")

# Try multiple models
models = {
    'Decision Tree': DecisionTreeClassifier(random_state=42),
    'Random Forest': RandomForestClassifier(random_state=42, n_jobs=-1),
    'Gradient Boosting': GradientBoostingClassifier(random_state=42)
}

print("\n🔍 Training and evaluating multiple models...")

best_model = None
best_score = 0
best_model_name = ""
results = {}

for model_name, model in models.items():
    print(f"\n📌 Training {model_name}...")
    
    # Simple cross-validation first
    cv_scores = cross_val_score(model, X_train, y_train, cv=5)
    print(f"  CV Accuracy: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")
    
    # Train the model
    model.fit(X_train, y_train)
    
    # Make predictions
    y_pred = model.predict(X_test)
    
    # Calculate accuracy
    accuracy = accuracy_score(y_test, y_pred)
    print(f"  Test Accuracy: {accuracy:.3f}")
    
    results[model_name] = {
        'model': model,
        'accuracy': accuracy,
        'cv_mean': cv_scores.mean(),
        'cv_std': cv_scores.std()
    }
    
    # Track best model
    if accuracy > best_score:
        best_score = accuracy
        best_model = model
        best_model_name = model_name

print(f"\n🏆 Best Model: {best_model_name}")
print(f"   Best Accuracy: {best_score:.3f}")

# Detailed evaluation of best model
print(f"\n📊 Detailed Evaluation of {best_model_name}:")
y_pred_best = best_model.predict(X_test)

print("\nClassification Report:")
print(classification_report(y_test, y_pred_best, 
                          target_names=label_encoder.classes_,
                          zero_division=0))

# Confusion Matrix
cm = confusion_matrix(y_test, y_pred_best)
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=label_encoder.classes_,
            yticklabels=label_encoder.classes_)
plt.title(f'Confusion Matrix - {best_model_name}')
plt.ylabel('Actual')
plt.xlabel('Predicted')
plt.tight_layout()
plt.savefig('visualizations/confusion_matrix.png')
plt.close()

# Feature importance (for tree-based models)
if hasattr(best_model, 'feature_importances_'):
    feature_importance = best_model.feature_importances_
    
    print("\n🔍 Feature Importance:")
    importance_df = pd.DataFrame({
        'feature': feature_columns,
        'importance': feature_importance
    }).sort_values('importance', ascending=False)
    
    for _, row in importance_df.iterrows():
        print(f"  {row['feature'].replace('_', ' ').title()}: {row['importance']:.3f}")
    
    # Visualize feature importance
    plt.figure(figsize=(10, 6))
    sns.barplot(data=importance_df, x='importance', y='feature')
    plt.title(f'Feature Importance - {best_model_name}')
    plt.xlabel('Importance')
    plt.tight_layout()
    plt.savefig('visualizations/feature_importance.png')
    plt.close()

# Save the best model and preprocessors
joblib.dump(best_model, 'model.pkl')
joblib.dump(label_encoder, 'label_encoder.pkl')
joblib.dump(scaler, 'scaler.pkl')
joblib.dump(feature_columns, 'feature_columns.pkl')

print("\n✅ Model and preprocessors saved successfully!")
print(f"📊 Best Model: {best_model_name}")
print(f"📊 Features: {feature_columns}")
print(f"🎯 Target classes: {list(label_encoder.classes_)}")

# Test with sample inputs using the best model
print("\n🧪 Testing model with sample inputs:")
test_cases = [
    {"name": "Excellent Student", "values": [95, 95, 95] + [18, 90, 4, 3][:len(feature_columns)-3]},
    {"name": "Good Student", "values": [85, 80, 85] + [14, 80, 3, 2][:len(feature_columns)-3]},
    {"name": "Average Student", "values": [65, 60, 70] + [8, 65, 2, 2][:len(feature_columns)-3]},
    {"name": "Poor Student", "values": [40, 35, 30] + [3, 40, 0, 1][:len(feature_columns)-3]},
]

for test_case in test_cases:
    # Create test input as DataFrame
    test_input = pd.DataFrame([test_case["values"]], columns=feature_columns)
    
    # Scale the input
    test_input_scaled = scaler.transform(test_input)
    
    # Make prediction
    pred_encoded = best_model.predict(test_input_scaled)[0]
    pred_class = label_encoder.inverse_transform([pred_encoded])[0]
    
    # Get probability
    if hasattr(best_model, 'predict_proba'):
        proba = best_model.predict_proba(test_input_scaled)[0]
        confidence = max(proba) * 100
    else:
        confidence = 100.0
    
    print(f"\n  📌 {test_case['name']}:")
    print(f"     Input: {test_case['values'][:3]}... (showing first 3 features)")
    print(f"     Prediction: {pred_class} (Confidence: {confidence:.1f}%)")

# Generate model comparison plot
if results:
    model_names = list(results.keys())
    accuracies = [results[name]['accuracy'] for name in model_names]
    cv_means = [results[name]['cv_mean'] for name in model_names]

    plt.figure(figsize=(10, 6))
    x = np.arange(len(model_names))
    width = 0.35

    plt.bar(x - width/2, accuracies, width, label='Test Accuracy', color='skyblue')
    plt.bar(x + width/2, cv_means, width, label='CV Accuracy', color='lightcoral')

    plt.xlabel('Models')
    plt.ylabel('Accuracy')
    plt.title('Model Performance Comparison')
    plt.xticks(x, model_names)
    plt.legend()
    plt.ylim(0, 1)
    plt.tight_layout()
    plt.savefig('visualizations/model_comparison.png')
    plt.close()
    print("\n📊 Model comparison plot saved to 'visualizations/model_comparison.png'")

print("\n✨ Training completed successfully!")
print(f"   Total time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)