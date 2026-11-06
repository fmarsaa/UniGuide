"""Builds xgboost_training_dataset_v4.csv from the same seed-42 students as v3.

The generator is rerun with seed 42; it now writes untaken subjects as NaN with a
0/1 took_ column. The result is compared with xgboost_training_dataset_v3.csv:
labels must be identical, every non-subject column must be identical, a taken
subject must keep its v3 grade points, and an untaken one must be the cell v3
filled with the mean grade points.

    python build_v4_dataset.py
"""
import os

import numpy as np
import pandas as pd

from kuccps import CLUSTER_OPTIONAL_SUBJECTS, FEATURE_COLUMN, ML_FEATURE_SUBJECTS, TOOK_COLUMN
from synthetic_data_generator import generate_dataset

HERE = os.path.dirname(os.path.abspath(__file__))
V3_CSV = os.path.join(HERE, "xgboost_training_dataset_v3.csv")
V4_CSV = os.path.join(HERE, "xgboost_training_dataset_v4.csv")


def main() -> None:
    v3 = pd.read_csv(V3_CSV)
    v4 = generate_dataset(seed=42)
    v4 = pd.read_csv(pd.io.common.StringIO(v4.to_csv(index=False)))

    print("\n=== Comparison with v3 ===")
    print(f"v3 rows: {len(v3)}, v4 rows: {len(v4)}")
    if len(v3) != len(v4) or list(v3["student_id"]) != list(v4["student_id"]):
        raise SystemExit("Row count or student_id order differs from v3.")
    label_differences = int((v3["programme_label"] != v4["programme_label"]).sum())
    print(f"Label differences: {label_differences}")

    subject_cols = [FEATURE_COLUMN[s] for s in ML_FEATURE_SUBJECTS]
    took_cols = [TOOK_COLUMN[s] for s in CLUSTER_OPTIONAL_SUBJECTS]
    other_cols = [c for c in v3.columns if c not in subject_cols]
    print(f"Columns added in v4: {[c for c in v4.columns if c not in v3.columns]}")
    print(f"Columns removed in v4: {[c for c in v3.columns if c not in v4.columns]}")
    print(f"Non-subject columns identical to v3 ({len(other_cols)}): {v3[other_cols].equals(v4[other_cols])}")

    print("\nNaN values per subject column (v4):")
    mismatches = 0
    for col in subject_cols:
        missing = v4[col].isna()
        taken_same = bool(np.array_equal(v4.loc[~missing, col].to_numpy(), v3.loc[~missing, col].to_numpy()))
        nan_was_mean = bool((v3.loc[missing, col] == v3.loc[missing, "mean_points"]).all())
        mismatches += (not taken_same) + (not nan_was_mean)
        print(f"  {col:<16} NaN: {int(missing.sum()):>5}   taken values equal v3: {taken_same}   "
              f"NaN cells were the mean in v3: {nan_was_mean}")

    print("\ntook_ columns (v4):")
    for subject in CLUSTER_OPTIONAL_SUBJECTS:
        took, col = TOOK_COLUMN[subject], FEATURE_COLUMN[subject]
        consistent = bool(((v4[took] == 0) == v4[col].isna()).all())
        print(f"  {took:<16} took=1: {int((v4[took] == 1).sum()):>5}   took=0: {int((v4[took] == 0).sum()):>5}   "
              f"took=0 exactly where {col} is NaN: {consistent}")
        mismatches += not consistent

    if label_differences or mismatches or not v3[other_cols].equals(v4[other_cols]):
        raise SystemExit("v4 does not match v3 as required; nothing was saved.")
    v4.to_csv(V4_CSV, index=False)
    print(f"\nSaved {V4_CSV} ({len(v4)} rows, {len(v4.columns)} columns)")
    print(f"Column list: {list(v4.columns)}")


if __name__ == "__main__":
    main()
