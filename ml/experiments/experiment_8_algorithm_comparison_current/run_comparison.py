"""Experiment 8 - Random Forest vs Histogram Gradient Boosting vs Logistic Regression
on the CURRENT dataset (53 classes, undecided profiles), repeated with several
cross-validation shuffles so the run-to-run variation is reported, not one lucky split.

Run from the repository root:  python ml/experiments/experiment_8_algorithm_comparison_current/run_comparison.py
Comparison only: it never writes rf_model_pipeline.pkl or model_metrics.json.
Results are saved after every model/seed, so a stopped run keeps what it finished.
"""
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime

import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.abspath(os.path.join(HERE, "..", "..", "..", "backend"))
sys.path.insert(0, BACKEND)
os.chdir(BACKEND)

from train_random_forest import (CATEGORICAL_FEATURES, DATASET_SIZE, FEATURE_COLUMNS,  # noqa: E402
                                 NUMERIC_FEATURES, TARGET_COLUMN)
from synthetic_data_generator import create_synthetic_dataset  # noqa: E402

SEEDS = [42, 43, 44]
RESULTS_PATH = os.path.join(HERE, "results.json")


def build(classifier):
    pre = ColumnTransformer([
        ("num", "passthrough", NUMERIC_FEATURES),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES),
    ])
    return Pipeline([("preprocessor", pre), ("classifier", classifier)])


MODELS = {
    "logistic_regression": lambda s: LogisticRegression(max_iter=2000, class_weight="balanced", random_state=s),
    "random_forest": lambda s: RandomForestClassifier(
        n_estimators=350, max_depth=None, min_samples_leaf=1, max_features="log2",
        class_weight="balanced_subsample", random_state=s, n_jobs=4),
    "gradient_boosting": lambda s: HistGradientBoostingClassifier(max_iter=300, random_state=s),
}


def git_commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=HERE, text=True).strip()
    except Exception:
        return "unknown"


def main():
    df = create_synthetic_dataset(DATASET_SIZE)
    X, y = df[FEATURE_COLUMNS], df[TARGET_COLUMN]
    data_hash = hashlib.sha256(pd.util.hash_pandas_object(df, index=False).values.tobytes()).hexdigest()
    record = {
        "started": datetime.now().isoformat(timespec="seconds"),
        "git_commit": git_commit(),
        "dataset": {"rows": len(df), "classes": int(y.nunique()), "sha256_of_row_hashes": data_hash,
                    "generator_size_argument": DATASET_SIZE},
        "cv": "5-fold StratifiedKFold out-of-fold predictions, shuffled; one run per seed",
        "seeds": SEEDS,
        "versions": {"python": platform.python_version(), "scikit-learn": sklearn.__version__,
                     "numpy": np.__version__, "pandas": pd.__version__},
        "majority_class_baseline": float(y.value_counts().max() / len(y)),
        "chance": float(1 / y.nunique()),
        "runs": {},
    }
    for name, make in MODELS.items():
        record["runs"][name] = []
        for seed in SEEDS:
            t = time.time()
            cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
            pred = cross_val_predict(build(make(seed)), X, y, cv=cv, n_jobs=1)
            row = {"seed": seed,
                   "accuracy": accuracy_score(y, pred),
                   "weighted_f1": f1_score(y, pred, average="weighted"),
                   "macro_f1": f1_score(y, pred, average="macro"),
                   "seconds": round(time.time() - t)}
            record["runs"][name].append(row)
            print(name, row, flush=True)
            with open(RESULTS_PATH, "w") as f:
                json.dump(record, f, indent=2)
    summary = {}
    for name, rows in record["runs"].items():
        summary[name] = {k: {"mean": float(np.mean([r[k] for r in rows])), "std": float(np.std([r[k] for r in rows]))}
                         for k in ("accuracy", "weighted_f1", "macro_f1")}
    record["summary"] = summary
    record["finished"] = datetime.now().isoformat(timespec="seconds")
    with open(RESULTS_PATH, "w") as f:
        json.dump(record, f, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
