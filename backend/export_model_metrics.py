"""Writes backend/model_metrics_v4.json, the summary the backend serves on
/api/health for the admin dashboard, from the metrics train_evaluate.py saved
in report_outputs_v4/metrics.json. Every number is copied from that file;
nothing is recomputed here. The figures are the XGBoost test-set results of
the training-split model (the deployed model itself is fitted on all rows and
is not evaluated).

Run after train_evaluate.py:  python backend/export_model_metrics.py
"""
import json
import os
import subprocess
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(os.path.dirname(HERE), "report_outputs_v4", "metrics.json")
TARGET = os.path.join(HERE, "model_metrics_v4.json")


def main():
    with open(SOURCE, encoding="utf-8") as f:
        metrics = json.load(f)
    detail = metrics["xgboost_test_detail"]
    try:
        commit = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=HERE, text=True).strip()
    except Exception:
        commit = "nogit"
    summary = {
        "model_type": "Extreme Gradient Boosting (XGBoost)",
        "model_version": f"xgb-v4-{datetime.fromtimestamp(os.path.getmtime(SOURCE)).strftime('%Y%m%d')}-{commit}",
        "model_file": "uniguide_xgb_v4.joblib",
        "accuracy": detail["accuracy"],
        "weighted_f1": detail["weighted_f1"],
        "macro_f1": detail["macro_f1"],
        "top3_accuracy": detail["top3_accuracy"],
        "evaluation_method": "Stratified 80/20 split (random_state=42); XGBoost fitted on the training rows and "
                             "evaluated once on the test rows. Deployment model refitted on all rows.",
        "n_train": metrics["dataset"]["n_train"],
        "n_test": metrics["dataset"]["n_test"],
        "n_classes": metrics["dataset"]["classes"],
        "source": os.path.relpath(SOURCE, os.path.dirname(HERE)),
    }
    with open(TARGET, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))
    print(f"Saved {TARGET}")


if __name__ == "__main__":
    main()
