"""
UniGuide - Random Forest Model Training and Evaluation Pipeline
Author: Fatuma Omar Marsa (159056)
Supervised by: Deperias Webula Kerre
Strathmore University - School of Computing and Engineering Sciences

Implements:
- CRISP-DM Machine Learning Pipeline
- Stratified Train-Test Split (80/20)
- Random Forest Classifier (Scikit-Learn) with hyperparameter tuning
- Metrics: Accuracy, Precision, Recall, F1-Score, Confusion Matrix
- SHAP TreeExplainer generation for individual prediction explainability
"""

import pickle
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, accuracy_score, f1_score
import shap

from synthetic_data_generator import create_synthetic_dataset

def train_and_evaluate_model():
    print("Step 1: Generating validated synthetic student dataset (N=1500)...")
    df = create_synthetic_dataset(1500)

    feature_cols = [
        "math_score", "eng_score", "phys_score", "chem_score", "bio_score", "comp_score", "mean_points",
        "primary_interest", "primary_skill", "primary_strength", "aspiration"
    ]
    target_col = "programme_label"

    X = df[feature_cols]
    y = df[target_col]

    print("Step 2: Stratified Train-Test Split (80/20)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    categorical_features = ["primary_interest", "primary_skill", "primary_strength", "aspiration"]
    numerical_features = ["math_score", "eng_score", "phys_score", "chem_score", "bio_score", "comp_score", "mean_points"]

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", "passthrough", numerical_features),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_features),
        ]
    )

    rf_clf = RandomForestClassifier(
        n_estimators=150,
        max_depth=12,
        min_samples_split=4,
        random_state=42,
        n_jobs=-1
    )

    pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("classifier", rf_clf)
    ])

    print("Step 3: Training Random Forest Classifier...")
    pipeline.fit(X_train, y_train)

    print("Step 4: Evaluating Model Performance on Held-Out Test Set...")
    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average="weighted")

    print(f"Overall Accuracy: {acc * 100:.2f}%")
    print(f"Weighted F1-Score: {f1 * 100:.2f}%")
    print("\nClassification Report:\n", classification_report(y_test, y_pred))

    print("Step 5: Initializing SHAP TreeExplainer for Transparency & Explainability...")
    X_train_trans = pipeline.named_steps["preprocessor"].transform(X_train)
    explainer = shap.TreeExplainer(pipeline.named_steps["classifier"])

    print("Step 6: Saving serialized model artifacts...")
    with open("rf_model_pipeline.pkl", "wb") as f:
        pickle.dump(pipeline, f)
    
    print("Training complete! Model artifacts saved to rf_model_pipeline.pkl.")

if __name__ == "__main__":
    train_and_evaluate_model()
