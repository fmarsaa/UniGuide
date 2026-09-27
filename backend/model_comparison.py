"""
UniGuide - Algorithm Comparison Experiment
Author: Fatuma Omar Marsa (159056)
Supervised by: Deperias Webula Kerre
Strathmore University - School of Computing and Engineering Sciences

Answers "why Random Forest specifically?" with evidence rather than
assertion. Trains Random Forest (with the Experiment 1b hyperparameters
already validated in train_random_forest.py), Histogram Gradient Boosting,
and Logistic Regression on the IDENTICAL dataset, features, and evaluation
methodology (5-fold StratifiedKFold out-of-fold cross_val_predict, same as
the primary reported metrics), so the comparison is apples-to-apples. This
is a comparison-only script - it does NOT overwrite rf_model_pipeline.pkl or
model_metrics.json; the deployed model is still produced by
train_random_forest.py.
"""

import json

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from kuccps import ML_FEATURE_SUBJECTS, FEATURE_COLUMN
from synthetic_data_generator import THIN_CLASS_FLOOR, TRAIT_FEATURE_COLUMNS, create_synthetic_dataset

NUMERIC_FEATURES = [FEATURE_COLUMN[s] for s in ML_FEATURE_SUBJECTS] + ["mean_points"] + TRAIT_FEATURE_COLUMNS
CATEGORICAL_FEATURES = ["aspiration"]
FEATURE_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES
TARGET_COLUMN = "programme_label"
DATASET_SIZE = 6000

# Experiment 1b's validated best Random Forest hyperparameters - not
# re-searched here, since the point is comparing algorithms, not re-tuning
# a model this script doesn't deploy.
RF_BEST_PARAMS = {
    "n_estimators": 350,
    "max_depth": None,
    "min_samples_leaf": 1,
    "max_features": "log2",
    "random_state": 42,
    "n_jobs": -1,
    "class_weight": "balanced_subsample",
}


def build_pipeline(classifier):
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", "passthrough", NUMERIC_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES),
        ]
    )
    return Pipeline(steps=[("preprocessor", preprocessor), ("classifier", classifier)])


def evaluate(name, pipeline, X, y, skf):
    y_pred = cross_val_predict(pipeline, X, y, cv=skf, n_jobs=-1)
    acc = accuracy_score(y, y_pred)
    f1 = f1_score(y, y_pred, average="weighted")
    macro_f1 = f1_score(y, y_pred, average="macro")
    report = classification_report(y, y_pred, output_dict=True, zero_division=0)
    print(f"\n{name}")
    print(f"  Accuracy: {acc * 100:.2f}%  |  Weighted F1: {f1 * 100:.2f}%  |  Macro F1: {macro_f1 * 100:.2f}%")
    return {"accuracy": acc, "weighted_f1": f1, "macro_f1": macro_f1, "classification_report": report}


def main():
    print(f"Generating the same Experiment 1b dataset (N={DATASET_SIZE} balanced-target profiles, floor={THIN_CLASS_FLOOR})...")
    df = create_synthetic_dataset(DATASET_SIZE)
    print(f"Total profiles: {len(df)}")

    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    results = {}

    results["random_forest"] = evaluate(
        "Random Forest (Experiment 1b hyperparameters)",
        build_pipeline(RandomForestClassifier(**RF_BEST_PARAMS)),
        X, y, skf,
    )

    results["gradient_boosting"] = evaluate(
        "Histogram Gradient Boosting (sklearn defaults + class balancing via sample_weight not applied - see note)",
        build_pipeline(HistGradientBoostingClassifier(random_state=42, max_iter=300)),
        X, y, skf,
    )

    results["logistic_regression"] = evaluate(
        "Logistic Regression (multinomial, balanced class weights)",
        build_pipeline(LogisticRegression(max_iter=2000, class_weight="balanced", random_state=42)),
        X, y, skf,
    )

    print("\n" + "=" * 70)
    print("SUMMARY (5-fold StratifiedKFold out-of-fold, same dataset/features)")
    print("=" * 70)
    for name, r in results.items():
        print(f"{name:25s}  accuracy={r['accuracy']*100:6.2f}%  weighted_f1={r['weighted_f1']*100:6.2f}%  macro_f1={r['macro_f1']*100:6.2f}%")

    with open("model_comparison_results.json", "w") as f:
        json.dump(
            {
                "dataset_size": len(df),
                "n_classes": int(y.nunique()),
                "evaluation_method": "5-fold StratifiedKFold cross_val_predict, out-of-fold, identical dataset/features across all three models",
                "results": results,
            },
            f,
            indent=2,
        )
    print("\nSaved to model_comparison_results.json")


if __name__ == "__main__":
    main()
