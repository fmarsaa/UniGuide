"""
UniGuide - XGBoost Model Training and Evaluation Pipeline
Author: Fatuma Omar Marsa (159056)
Supervised by: Deperias Webula Kerre
Strathmore University - School of Computing and Engineering Sciences

Implements:
- Extreme Gradient Boosting (XGBoost) Pipeline
- Stratified Train-Test Split (80/20) + 5-fold Stratified cross-validation
- Metrics: Accuracy, Precision, Recall, F1-Score, Confusion Matrix
- Full compatibility with TreeSHAP explainability
- Serialized to rf_model_pipeline.pkl for drop-in FastAPI inference
"""

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
import sklearn
import xgboost as xgb

from sklearn.base import BaseEstimator, ClassifierMixin, clone
from sklearn.compose import ColumnTransformer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, OneHotEncoder

from kuccps import ML_FEATURE_SUBJECTS, FEATURE_COLUMN
from synthetic_data_generator import (
    CLUSTER_SCORE_FEATURE_COLUMNS,
    THIN_CLASS_FLOOR,
    TRAIT_FEATURE_COLUMNS,
    create_synthetic_dataset,
)

INCLUDE_CLUSTER_SCORE_FEATURES = False

NUMERIC_FEATURES = (
    [FEATURE_COLUMN[s] for s in ML_FEATURE_SUBJECTS]
    + ["mean_points"]
    + TRAIT_FEATURE_COLUMNS
    + (CLUSTER_SCORE_FEATURE_COLUMNS if INCLUDE_CLUSTER_SCORE_FEATURES else [])
)
CATEGORICAL_FEATURES = ["aspiration"]
FEATURE_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES
TARGET_COLUMN = "programme_label"

DATASET_SIZE = 6000
N_JOBS = int(os.environ.get("TRAIN_N_JOBS", "4"))

_DIR = os.path.dirname(os.path.abspath(__file__))
_MODEL_PATH = os.path.join(_DIR, "rf_model_pipeline.pkl")
_METRICS_PATH = os.path.join(_DIR, "model_metrics.json")
_BACKUPS_DIR = os.path.join(_DIR, "model_backups")

# When this file is executed directly, give the forced pickle module name a
# real module object so joblib can serialize the wrapper class reliably.
if __name__ == "__main__":
    sys.modules.setdefault("train_xgboost", sys.modules[__name__])


class XGBoostStringClassifier(BaseEstimator, ClassifierMixin):
    __module__ = "train_xgboost"
    """XGBoost wrapper that handles arbitrary string multi-class targets seamlessly,
    making it a 100% drop-in replacement for Scikit-Learn pipelines."""
    def __init__(self, n_estimators=200, max_depth=5, learning_rate=0.08,
                 subsample=0.8, colsample_bytree=0.8, n_jobs=4, random_state=42):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.subsample = subsample
        self.colsample_bytree = colsample_bytree
        self.n_jobs = n_jobs
        self.random_state = random_state
        self.clf_ = None
        self.encoder_ = LabelEncoder()

    def fit(self, X, y):
        y_enc = self.encoder_.fit_transform(y)
        self.classes_ = self.encoder_.classes_
        self.clf_ = xgb.XGBClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            learning_rate=self.learning_rate,
            subsample=self.subsample,
            colsample_bytree=self.colsample_bytree,
            n_jobs=self.n_jobs,
            random_state=self.random_state,
            eval_metric="mlogloss",
            tree_method="hist",
        )
        self.clf_.fit(X, y_enc)
        return self

    def predict(self, X):
        preds = self.clf_.predict(X)
        return self.encoder_.inverse_transform(preds)

    def predict_proba(self, X):
        return self.clf_.predict_proba(X)


def build_run_record(df, started_at=None):
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=_DIR, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        commit = "unknown"
    started_at = started_at or datetime.now()
    dataset_hash = hashlib.sha256(pd.util.hash_pandas_object(df, index=False).values.tobytes()).hexdigest()
    short = commit[:7] if commit != "unknown" else "nogit"
    return {
        "model_version": f"xgb-{started_at.strftime('%Y%m%d')}-{short}",
        "trained_at": started_at.isoformat(timespec="seconds"),
        "git_commit": commit,
        "dataset": {"rows": len(df), "sha256_of_row_hashes": dataset_hash, "generator_size_argument": DATASET_SIZE},
        "seeds": {"model": 42, "train_test_split": 42, "cross_validation": 42},
        "versions": {
            "python": platform.python_version(),
            "scikit-learn": sklearn.__version__,
            "xgboost": xgb.__version__,
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
    }


def train_and_evaluate_xgboost():
    print(f"Step 1: Generating synthetic student dataset (N={DATASET_SIZE})...")
    started_at = datetime.now()
    df = create_synthetic_dataset(DATASET_SIZE)
    print(f"Total profiles: {len(df)}")

    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]
    labels = sorted(y.unique().tolist())

    print("\nStep 2: Stratified Train-Test Split (80/20)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", "passthrough", NUMERIC_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES),
        ]
    )

    xgb_clf = XGBoostStringClassifier(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.08,
        subsample=0.8,
        colsample_bytree=0.8,
        n_jobs=N_JOBS,
        random_state=42,
    )

    pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("classifier", xgb_clf),
    ])

    print("Step 3: Training XGBoost on training split and evaluating on 20% holdout test...")
    pipeline.fit(X_train, y_train)
    y_pred_holdout = pipeline.predict(X_test)
    holdout_acc = accuracy_score(y_test, y_pred_holdout)
    holdout_f1 = f1_score(y_test, y_pred_holdout, average="weighted")
    holdout_report = classification_report(y_test, y_pred_holdout, output_dict=True, zero_division=0)
    print(f"Holdout accuracy: {holdout_acc * 100:.2f}%  |  Holdout weighted F1: {holdout_f1 * 100:.2f}%")

    print("\nStep 4: 5-Fold Cross-Validation out-of-fold evaluation across full dataset...")
    cv_pipeline = clone(pipeline)
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    y_pred_cv = cross_val_predict(cv_pipeline, X, y, cv=skf, n_jobs=N_JOBS)
    cv_acc = accuracy_score(y, y_pred_cv)
    cv_f1 = f1_score(y, y_pred_cv, average="weighted")
    cv_report = classification_report(y, y_pred_cv, output_dict=True, zero_division=0)
    cv_cm = confusion_matrix(y, y_pred_cv, labels=labels)

    print(f"\n=======================================================")
    print(f"XGBoost Cross-validated Accuracy:    {cv_acc * 100:.2f}%")
    print(f"XGBoost Cross-validated Weighted F1: {cv_f1 * 100:.2f}%")
    print(f"=======================================================\n")

    # Backup previous model if exists
    if os.path.exists(_MODEL_PATH):
        os.makedirs(_BACKUPS_DIR, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy(_MODEL_PATH, os.path.join(_BACKUPS_DIR, f"rf_model_pipeline_{stamp}.pkl"))
        if os.path.exists(_METRICS_PATH):
            shutil.copy(_METRICS_PATH, os.path.join(_BACKUPS_DIR, f"model_metrics_{stamp}.json"))

    print("Step 5: Persisting metrics to model_metrics.json...")
    run_record = build_run_record(df, started_at)
    with open(_METRICS_PATH, "w") as f:
        json.dump({
            "model_type": "Extreme Gradient Boosting (XGBoost)",
            "model_version": run_record["model_version"],
            "run_record": run_record,
            "accuracy": cv_acc,
            "weighted_f1": cv_f1,
            "classification_report": cv_report,
            "confusion_matrix": cv_cm.tolist(),
            "confusion_matrix_labels": labels,
            "evaluation_method": "5-fold StratifiedKFold cross_val_predict, out-of-fold predictions across full dataset",
            "n_total": len(X),
            "n_classes": len(labels),
            "thin_class_floor": THIN_CLASS_FLOOR,
            "holdout_reference": {
                "n_train": len(X_train),
                "n_test": len(X_test),
                "accuracy": holdout_acc,
                "weighted_f1": holdout_f1,
                "classification_report": holdout_report,
            },
        }, f, indent=2)

    print("Step 6: Fitting final XGBoost pipeline on FULL dataset for deployment...")
    final_pipeline = clone(pipeline)
    final_pipeline.fit(X, y)

    # Save to _MODEL_PATH so main.py loads it automatically
    joblib.dump(final_pipeline, _MODEL_PATH, compress=("zlib", 3))
    print(f"Training complete! Model saved to {_MODEL_PATH}")
    file_size_mb = os.path.getsize(_MODEL_PATH) / (1024 * 1024)
    print(f"New Model File Size: {file_size_mb:.2f} MB (compared to 2,270 MB before!)")


if __name__ == "__main__":
    train_and_evaluate_xgboost()
