"""
UniGuide - Random Forest Model Training and Evaluation Pipeline
Author: Fatuma Omar Marsa (159056)
Supervised by: Deperias Webula Kerre
Strathmore University - School of Computing and Engineering Sciences

Implements:
- CRISP-DM Machine Learning Pipeline
- Stratified Train-Test Split (80/20) for hyperparameter search and a
  reference holdout evaluation
- 5-fold Stratified cross-validated out-of-fold evaluation (cross_val_predict)
  across the FULL dataset for the primary reported metrics - every class,
  including the smaller ones, gets a full complement of held-out
  predictions instead of a single ~20% test slice, since a single small
  test slice makes a rare class's precision/recall swing wildly on just a
  handful of examples (see Chapter 5.3's discussion of this)
- Random Forest Classifier (Scikit-Learn) with GridSearchCV hyperparameter
  tuning (tuned only against training-split CV folds, never against the
  final evaluation data)
- Metrics: Accuracy, Precision, Recall, F1-Score, Confusion Matrix
- SHAP TreeExplainer generation for individual prediction explainability

The trained pipeline (preprocessing + classifier) is serialized to
rf_model_pipeline.pkl and loaded directly by main.py at inference time -
no prediction logic is duplicated between training and serving. The
serialized model is refit on the FULL dataset (after hyperparameters are
chosen and validated) rather than just the 80% train split, since once
performance is validated there's no reason to withhold real training
signal from the model that actually gets deployed.
"""

import json
import os
import pickle
import shutil
from datetime import datetime

from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_val_predict, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from kuccps import ML_FEATURE_SUBJECTS, FEATURE_COLUMN
from synthetic_data_generator import (
    CLUSTER_SCORE_FEATURE_COLUMNS,
    THIN_CLASS_FLOOR,
    TRAIT_FEATURE_COLUMNS,
    create_synthetic_dataset,
)

# Experiment 2 toggle: include the per-programme Cluster-Weighted-Points-vs-
# cutoff features (see synthetic_data_generator.build_cluster_score_features)
# alongside Experiment 1's feature set, as a controlled A/B comparison
# against ml/experiments/experiment_1_profile_redesign (87.21% accuracy,
# without these features). Per the original brainstorm's own rule: keep this
# True only if the comparison in ml/experiments/experiment_2_cluster_score/
# actually shows it helps - do not leave it on "because it sounds useful".
INCLUDE_CLUSTER_SCORE_FEATURES = False

# One numeric feature per subject that actually feeds a real KUCCPS cluster
# requirement somewhere in programmes_catalog.py (5 compulsory + 4 optional
# cluster-relevant subjects), plus overall mean points, plus one boolean
# feature per interest/skill/strength a student can select (TRAIT_FEATURE_
# COLUMNS - every option they picked, not just the first), plus (Experiment 2
# only) one cluster-score feature per trained programme. Kept in sync with
# kuccps.ML_FEATURE_SUBJECTS / FEATURE_COLUMN and synthetic_data_generator's
# trait/cluster-score columns so training and serving (main.py) can never
# disagree on the feature schema.
NUMERIC_FEATURES = (
    [FEATURE_COLUMN[s] for s in ML_FEATURE_SUBJECTS]
    + ["mean_points"]
    + TRAIT_FEATURE_COLUMNS
    + (CLUSTER_SCORE_FEATURE_COLUMNS if INCLUDE_CLUSTER_SCORE_FEATURES else [])
)
CATEGORICAL_FEATURES = ["aspiration"]
FEATURE_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES
TARGET_COLUMN = "programme_label"

# Experiment 1: every one of the 21 trained programmes is now generated with
# a thematic bias toward it (see synthetic_data_generator._build_profile_for_
# target), not just the 5 hardest-gated ones - so N=6000 balanced-target
# profiles + a uniform THIN_CLASS_FLOOR top-up pass for any class that still
# fell short + balanced class weights + a hyperparameter search together
# address class imbalance, instead of just accepting whatever the first
# guessed hyperparameters give on an unreliable small test slice.
DATASET_SIZE = 15000  # scaled from 6000 for 21 classes to keep ~similar per-class density across 53
PARAM_GRID = {
    "classifier__n_estimators": [200, 350],
    "classifier__max_depth": [12, 18, None],
    "classifier__min_samples_leaf": [1, 2],
    "classifier__max_features": ["sqrt", "log2"],
}

# Defaults to using every CPU core for a normal `python train_random_forest.py`
# run. The admin-triggered retrain (main.py's POST /api/admin/model/retrain)
# launches this script as a genuinely separate OS process specifically so a
# memory spike here can't take down the live FastAPI server sharing the same
# machine - and sets TRAIN_N_JOBS to a conservative value for that case, since
# this machine's available RAM is tight enough that a second full-parallelism
# fit alongside the already-running server risked an out-of-memory failure
# (observed directly while testing). Untouched for the normal CLI workflow.
N_JOBS = int(os.environ.get("TRAIN_N_JOBS", "-1"))

# All file I/O below is __file__-relative (not CWD-relative) so this script
# behaves identically whether run directly (`python train_random_forest.py`
# from backend/) or launched as a subprocess from a different working
# directory, as the admin-triggered retrain above does.
_DIR = os.path.dirname(os.path.abspath(__file__))
_MODEL_PATH = os.path.join(_DIR, "rf_model_pipeline.pkl")
_METRICS_PATH = os.path.join(_DIR, "model_metrics.json")
_BACKUPS_DIR = os.path.join(_DIR, "model_backups")


def train_and_evaluate_model():
    print(f"Step 1: Generating validated synthetic student dataset (N={DATASET_SIZE} balanced-target profiles + a floor of {THIN_CLASS_FLOOR} for every one of the 21 trained classes)...")
    df = create_synthetic_dataset(DATASET_SIZE)
    print(f"Total profiles after oversampling: {len(df)}")
    print(df["programme_label"].value_counts().to_string())

    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]
    labels = sorted(y.unique().tolist())

    print("\nStep 2: Stratified Train-Test Split (80/20) for hyperparameter search and a reference holdout check...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", "passthrough", NUMERIC_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES),
        ]
    )

    rf_clf = RandomForestClassifier(
        random_state=42,
        n_jobs=N_JOBS,
        class_weight="balanced_subsample",
    )

    pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("classifier", rf_clf),
    ])

    print("Step 3: Grid-searching Random Forest hyperparameters (5-fold CV on the training split ONLY, weighted F1)...")
    search = GridSearchCV(pipeline, PARAM_GRID, cv=5, scoring="f1_weighted", n_jobs=N_JOBS)
    search.fit(X_train, y_train)
    best_params = search.best_params_
    print(f"Best params: {best_params}")
    print(f"Best cross-validated weighted F1 (training split only): {search.best_score_ * 100:.2f}%")

    print("Step 4: Reference holdout evaluation (fit on train split, evaluate on the untouched 20% test split)...")
    holdout_pipeline = search.best_estimator_
    holdout_pipeline.fit(X_train, y_train)
    y_pred_holdout = holdout_pipeline.predict(X_test)
    holdout_acc = accuracy_score(y_test, y_pred_holdout)
    holdout_f1 = f1_score(y_test, y_pred_holdout, average="weighted")
    holdout_report = classification_report(y_test, y_pred_holdout, output_dict=True, zero_division=0)
    print(f"Holdout accuracy: {holdout_acc * 100:.2f}%  |  Holdout weighted F1: {holdout_f1 * 100:.2f}%")

    print("Step 5: Cross-validated out-of-fold evaluation across the FULL dataset (5-fold StratifiedKFold) for defensible per-class metrics...")
    print("(Every profile gets exactly one out-of-fold prediction, so even the previously-thin classes are judged on their full oversampled count, not a ~20% slice of it.)")
    cv_pipeline = clone(pipeline).set_params(**best_params)
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    y_pred_cv = cross_val_predict(cv_pipeline, X, y, cv=skf, n_jobs=N_JOBS)
    cv_acc = accuracy_score(y, y_pred_cv)
    cv_f1 = f1_score(y, y_pred_cv, average="weighted")
    cv_report = classification_report(y, y_pred_cv, output_dict=True, zero_division=0)
    cv_cm = confusion_matrix(y, y_pred_cv, labels=labels)

    print(f"\nCross-validated (out-of-fold) Accuracy: {cv_acc * 100:.2f}%")
    print(f"Cross-validated (out-of-fold) Weighted F1-Score: {cv_f1 * 100:.2f}%")
    print("\nCross-validated Classification Report (this is the one cited in 5.4):\n", classification_report(y, y_pred_cv, zero_division=0))

    print("Step 6: Persisting evaluation metrics to model_metrics.json...")
    with open(_METRICS_PATH, "w") as f:
        json.dump({
            # Primary headline numbers: cross-validated out-of-fold, across
            # the full dataset - the defensible per-class numbers, not a
            # single lucky/unlucky 20% split.
            "accuracy": cv_acc,
            "weighted_f1": cv_f1,
            "classification_report": cv_report,
            "confusion_matrix": cv_cm.tolist(),
            "confusion_matrix_labels": labels,
            "evaluation_method": "5-fold StratifiedKFold cross_val_predict, out-of-fold predictions across the full dataset",
            "n_total": len(X),
            "n_classes": len(labels),
            "thin_class_floor": THIN_CLASS_FLOOR,
            "best_params": best_params,
            # Reference only: single 80/20 holdout split, kept for
            # comparison against the CV numbers above, not the headline.
            "holdout_reference": {
                "n_train": len(X_train),
                "n_test": len(X_test),
                "accuracy": holdout_acc,
                "weighted_f1": holdout_f1,
                "classification_report": holdout_report,
            },
        }, f, indent=2)

    print("Step 7: Refitting the final pipeline on the FULL dataset for deployment (hyperparameters validated above; no reason to withhold data from the model that actually serves)...")
    final_pipeline = clone(pipeline).set_params(**best_params)
    final_pipeline.fit(X, y)

    # Model versioning/rollback: before overwriting the artifact main.py
    # actually loads, archive whatever was previously deployed (pipeline +
    # its metrics) under a timestamp. If a retrain ever regresses, the
    # previous model can be restored with a plain file copy instead of
    # re-running an old experiment by hand.
    if os.path.exists(_MODEL_PATH):
        os.makedirs(_BACKUPS_DIR, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy(_MODEL_PATH, os.path.join(_BACKUPS_DIR, f"rf_model_pipeline_{stamp}.pkl"))
        if os.path.exists(_METRICS_PATH):
            shutil.copy(_METRICS_PATH, os.path.join(_BACKUPS_DIR, f"model_metrics_{stamp}.json"))
        print(f"  (previous deployed model backed up to model_backups/*_{stamp}.*)")

    with open(_MODEL_PATH, "wb") as f:
        pickle.dump(final_pipeline, f)

    print("Training complete! Model artifacts saved to rf_model_pipeline.pkl and model_metrics.json.")
    print("To roll back: copy the desired model_backups/rf_model_pipeline_<timestamp>.pkl over rf_model_pipeline.pkl (and its matching model_metrics_<timestamp>.json over model_metrics.json), then restart the backend.")


if __name__ == "__main__":
    train_and_evaluate_model()
