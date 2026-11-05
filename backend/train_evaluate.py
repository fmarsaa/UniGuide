"""
UniGuide - Train and evaluate the skills-free XGBoost model (v2)
Author: Fatuma Omar Marsa (159056)

Protocol (every reported number comes from this script's output):
1. Load the v2 dataset (no skl_ columns) and select the model features.
2. One stratified 80/20 split, random_state=42.
3. Logistic Regression, Random Forest, Histogram Gradient Boosting and XGBoost
   compared with stratified 5-fold cross-validation on the TRAINING rows only.
4. Each model fitted on the training rows and evaluated ONCE on the test rows.
5. Detailed XGBoost test metrics, figures and metrics.json from the
   training-split model.
6. The same split / CV / test protocol for XGBoost on the OLD dataset (which
   still has the skl_ skill columns), for a side-by-side comparison.
7. Only after evaluation: XGBoost refitted on ALL rows and saved as
   uniguide_xgb_v2.joblib for deployment. That model is never used for any
   reported number.

Run from the repository root:  python backend/train_evaluate.py

    python backend/train_evaluate.py --deploy-only
fits only the deployment model (step 7: same features and hyperparameters, all
rows) without any evaluation, for testing the app before the full run.
"""

import os
for v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(v, "1")

import json
import sys
import time
from collections import Counter

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xgboost as xgb
from matplotlib.colors import LinearSegmentedColormap
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, classification_report, confusion_matrix, f1_score,
                             precision_score, recall_score)
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from kuccps import FEATURE_COLUMN, ML_FEATURE_SUBJECTS  # noqa: E402
from programmes_catalog import CATALOG_BY_TITLE  # noqa: E402
from synthetic_data_generator import TRAIT_COLUMN_INFO  # noqa: E402
from train_xgboost import XGBoostStringClassifier  # noqa: E402

NEW_DATASET = os.path.join(HERE, "xgboost_training_dataset_v2_noskills.csv")
OLD_DATASET = os.path.join(HERE, "xgboost_training_dataset.csv")
MODEL_OUT = os.path.join(HERE, "uniguide_xgb_v2.joblib")
OUT_DIR = os.path.join(ROOT, "report_outputs_v2")
TARGET = "programme_label"
SEED = 42
LEAKAGE_THRESHOLD = 0.97
ICS = "Bachelor of Science in Informatics and Computer Science"

# Reference palette (dataviz skill, light surface): categorical slots 1-3 and the blue sequential ramp.
SURFACE, INK, INK_2 = "#fcfcfb", "#0b0b0b", "#52514e"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]
BLUE = "#2a78d6"
SEQ_BLUE = LinearSegmentedColormap.from_list(
    "seq_blue", [SURFACE, "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"])
plt.rcParams.update({
    "font.family": "serif", "font.size": 9, "axes.edgecolor": INK_2, "axes.labelcolor": INK,
    "xtick.color": INK_2, "ytick.color": INK_2, "text.color": INK, "axes.spines.top": False,
    "axes.spines.right": False, "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
})

SUBJECT_LABEL = {
    "Mathematics": "Maths grade", "English": "English grade", "Kiswahili": "Kiswahili grade",
    "Chemistry": "Chemistry grade", "Biology": "Biology grade", "Physics": "Physics grade",
    "History": "History grade", "Business Studies": "Business Studies grade", "Geography": "Geography grade",
}


def log(*args):
    print(*args, flush=True)


def select_features(df, include_skills=False):
    subjects = [FEATURE_COLUMN[s] for s in ML_FEATURE_SUBJECTS]
    traits = [c for c in df.columns if c.startswith("int_") or c.startswith("str_")]
    skills = [c for c in df.columns if c.startswith("skl_")] if include_skills else []
    numeric = subjects + ["mean_points"] + traits + skills
    categorical = ["aspiration"]
    return numeric, categorical


def preprocessor(numeric, categorical, scale=False):
    return ColumnTransformer([
        ("num", StandardScaler() if scale else "passthrough", numeric),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical),
    ])


def make_xgb():
    return XGBoostStringClassifier(n_estimators=200, max_depth=5, learning_rate=0.08, subsample=0.8,
                                   colsample_bytree=0.8, n_jobs=4, random_state=SEED)


def build_models(numeric, categorical):
    return {
        "Logistic Regression": Pipeline([
            ("preprocessor", preprocessor(numeric, categorical, scale=True)),
            ("classifier", LogisticRegression(max_iter=2000, class_weight="balanced", random_state=SEED))]),
        "Random Forest": Pipeline([
            ("preprocessor", preprocessor(numeric, categorical)),
            ("classifier", RandomForestClassifier(n_estimators=350, max_features="log2",
                                                  class_weight="balanced_subsample", random_state=SEED, n_jobs=2))]),
        "Histogram Gradient Boosting": Pipeline([
            ("preprocessor", preprocessor(numeric, categorical)),
            ("classifier", HistGradientBoostingClassifier(max_iter=300, random_state=SEED))]),
        "XGBoost": Pipeline([
            ("preprocessor", preprocessor(numeric, categorical)),
            ("classifier", make_xgb())]),
    }


def cv_scores(model, X, y):
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    res = cross_validate(model, X, y, cv=cv, n_jobs=1,
                         scoring={"accuracy": "accuracy", "macro_f1": "f1_macro", "weighted_f1": "f1_weighted"})
    return {k: {"mean": float(np.mean(res[f"test_{k}"])), "std": float(np.std(res[f"test_{k}"])),
                "folds": [float(v) for v in res[f"test_{k}"]]}
            for k in ("accuracy", "macro_f1", "weighted_f1")}


def test_scores(y_true, y_pred):
    return {"accuracy": float(accuracy_score(y_true, y_pred)),
            "macro_f1": float(f1_score(y_true, y_pred, average="macro")),
            "weighted_f1": float(f1_score(y_true, y_pred, average="weighted"))}


def top_k_accuracy(pipeline, X, y, k=3):
    proba = pipeline.predict_proba(X)
    classes = np.asarray(pipeline.classes_)
    top = np.argsort(-proba, axis=1)[:, :k]
    return float(np.mean([yt in classes[row] for yt, row in zip(np.asarray(y), top)]))


def field_of(title):
    """KUCCPS cluster number from the catalogue's clusterGroup, e.g. 'Cluster 2'.
    Several programmes share a number under slightly different wording, so the
    number alone defines the field; 'Cluster 6/7' is grouped with Cluster 6."""
    group = CATALOG_BY_TITLE[title]["clusterGroup"]
    number = group.split(":")[0].replace("Cluster", "").strip().split("/")[0]
    return f"Cluster {int(number)}"


def field_names():
    names = {}
    for p in CATALOG_BY_TITLE.values():
        names.setdefault(field_of(p["title"]), Counter())[p["clusterGroup"].split(":", 1)[1].strip()] += 1
    return {f: c.most_common(1)[0][0] for f, c in names.items()}


def short(title):
    return (title.replace("Bachelor of Science in ", "BSc ").replace("Bachelor of Arts in ", "BA ")
            .replace("Bachelor of Engineering in ", "BEng ").replace("Bachelor of ", "B. "))


def readable(feature):
    prefix, _, raw = feature.partition("__")
    if prefix == "cat":
        return "Aspiration: " + raw[len("aspiration_"):]
    for subject, col in FEATURE_COLUMN.items():
        if raw == col:
            return SUBJECT_LABEL[subject]
    if raw == "mean_points":
        return "Mean grade points"
    if raw in TRAIT_COLUMN_INFO:
        _, kind, label = TRAIT_COLUMN_INFO[raw]
        return f"{kind}: {label}"
    return raw


def save(fig, name):
    path = os.path.join(OUT_DIR, name)
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    log(f"Saved figure: {path}")
    return path


def hbar(values, labels, xlabel, title, name, height=None):
    fig, ax = plt.subplots(figsize=(6.6, height or max(3.0, 0.24 * len(values) + 0.8)))
    ax.barh(range(len(values)), values, color=BLUE, height=0.7)
    ax.set_yticks(range(len(values)))
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlabel(xlabel)
    ax.set_title(title, loc="left", fontsize=10)
    ax.grid(axis="x", color="#e4e3df", linewidth=0.6)
    ax.set_axisbelow(True)
    return save(fig, name)


def matrix_figure(cm, labels, title, name, size, annotate):
    row_sums = cm.sum(axis=1, keepdims=True)
    norm = np.divide(cm, row_sums, out=np.zeros_like(cm, dtype=float), where=row_sums > 0)
    fig, ax = plt.subplots(figsize=(size, size))
    im = ax.imshow(norm, cmap=SEQ_BLUE, vmin=0, vmax=1)
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    fs = 8 if annotate else 4.5
    ax.set_xticklabels(labels, rotation=90, fontsize=fs)
    ax.set_yticklabels(labels, fontsize=fs)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title(title, loc="left", fontsize=10)
    ax.spines[:].set_visible(False)
    if annotate:
        for i in range(len(labels)):
            for j in range(len(labels)):
                if cm[i, j]:
                    ax.text(j, i, int(cm[i, j]), ha="center", va="center", fontsize=6.5,
                            color=SURFACE if norm[i, j] > 0.5 else INK)
    cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cb.set_label("Share of the true class (row-normalised)")
    return save(fig, name)


def deploy_only():
    df = pd.read_csv(NEW_DATASET)
    numeric, categorical = select_features(df)
    features = numeric + categorical
    forbidden = [c for c in features if c.startswith(("skl_", "clsc_")) or c == "student_id"]
    assert not forbidden, f"forbidden features selected: {forbidden}"
    log(f"Dataset: {NEW_DATASET}")
    log(f"Rows: {len(df)}  Classes: {df[TARGET].nunique()}")
    log(f"Feature count (before one-hot): {len(features)} ({len(numeric)} numeric + {len(categorical)} categorical)")
    log("Feature list:")
    for f in features:
        log(f"  {f}")
    log("XGBoost: n_estimators=200, max_depth=5, learning_rate=0.08, subsample=0.8, colsample_bytree=0.8, "
        "tree_method=hist, random_state=42")
    t = time.time()
    final = build_models(numeric, categorical)["XGBoost"].fit(df[features], df[TARGET])
    log(f"Training time: {time.time() - t:.1f}s")
    n_after = len(final.named_steps["preprocessor"].get_feature_names_out())
    log(f"Feature count after one-hot: {n_after}")
    log(f"Class count: {len(final.classes_)}")
    joblib.dump(final, MODEL_OUT, compress=("zlib", 3))
    log(f"Saved deployment model: {MODEL_OUT} ({os.path.getsize(MODEL_OUT) / 1024 / 1024:.2f} MB)")
    log("No evaluation was run; this model is for app testing and deployment only.")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    started = time.time()
    metrics = {"protocol": {"split": "stratified 80/20, random_state=42",
                            "cv": "StratifiedKFold(5, shuffle=True, random_state=42) on training rows only",
                            "test": "each model fitted on training rows, evaluated once on test rows"}}

    # ------------------------------------------------------------------ data
    df = pd.read_csv(NEW_DATASET)
    log(f"Dataset: {NEW_DATASET}")
    log(f"Rows: {len(df)}  Columns: {len(df.columns)}  Classes: {df[TARGET].nunique()}")
    numeric, categorical = select_features(df)
    features = numeric + categorical
    forbidden = [c for c in features if c.startswith(("skl_", "clsc_")) or c == "student_id"]
    assert not forbidden, f"forbidden features selected: {forbidden}"
    log(f"Feature count (before one-hot): {len(features)} "
        f"({len(numeric)} numeric + {len(categorical)} categorical)")
    log("Feature list:")
    for f in features:
        log(f"  {f}")
    log(f"Aspiration categories (one-hot): {df['aspiration'].nunique()}")

    X, y = df[features], df[TARGET]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=SEED, stratify=y)
    log(f"\nSplit sizes: train={len(X_train)}  test={len(X_test)}")
    metrics["dataset"] = {"path": os.path.relpath(NEW_DATASET, ROOT), "rows": len(df),
                          "classes": int(y.nunique()), "n_train": len(X_train), "n_test": len(X_test),
                          "features": features}

    # ------------------------------------------------------------ CV on train
    models = build_models(numeric, categorical)
    metrics["cv_train"] = {}
    log("\n=== Stratified 5-fold CV on training rows only ===")
    for name, model in models.items():
        t = time.time()
        res = cv_scores(clone(model), X_train, y_train)
        metrics["cv_train"][name] = res
        log(f"{name:30s} accuracy {res['accuracy']['mean']:.4f} +/- {res['accuracy']['std']:.4f} | "
            f"macro-F1 {res['macro_f1']['mean']:.4f} +/- {res['macro_f1']['std']:.4f} | "
            f"weighted F1 {res['weighted_f1']['mean']:.4f} +/- {res['weighted_f1']['std']:.4f} "
            f"({time.time() - t:.0f}s)")

    # -------------------------------------------------------------- test once
    metrics["test"] = {}
    fitted = {}
    log("\n=== Fitted on training rows, evaluated once on test rows ===")
    for name, model in models.items():
        t = time.time()
        fitted[name] = clone(model).fit(X_train, y_train)
        res = test_scores(y_test, fitted[name].predict(X_test))
        metrics["test"][name] = res
        log(f"{name:30s} accuracy {res['accuracy']:.4f} | macro-F1 {res['macro_f1']:.4f} | "
            f"weighted F1 {res['weighted_f1']:.4f} ({time.time() - t:.0f}s)")

    above = {n: r["accuracy"] for n, r in metrics["test"].items() if r["accuracy"] > LEAKAGE_THRESHOLD}
    if above:
        log(f"\nSTOP: test accuracy above {LEAKAGE_THRESHOLD:.0%} for {above}. Possible leakage; "
            "nothing further is produced and no model is saved.")
        with open(os.path.join(OUT_DIR, "metrics.json"), "w") as f:
            json.dump(metrics, f, indent=2)
        sys.exit(2)

    # ------------------------------------------------------ XGBoost in detail
    xgb_pipe = fitted["XGBoost"]
    y_pred = xgb_pipe.predict(X_test)
    labels = sorted(y.unique())
    report = classification_report(y_test, y_pred, labels=labels, output_dict=True, zero_division=0)
    cm = confusion_matrix(y_test, y_pred, labels=labels)
    detail = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "macro_f1": float(f1_score(y_test, y_pred, average="macro")),
        "weighted_precision": float(precision_score(y_test, y_pred, average="weighted", zero_division=0)),
        "weighted_recall": float(recall_score(y_test, y_pred, average="weighted", zero_division=0)),
        "weighted_f1": float(f1_score(y_test, y_pred, average="weighted")),
        "top3_accuracy": top_k_accuracy(xgb_pipe, X_test, y_test, 3),
    }
    log("\n=== XGBoost test-set detail ===")
    for k, v in detail.items():
        log(f"{k:20s} {v:.4f}")

    recalls = sorted(((t, report[t]["recall"], int(report[t]["support"])) for t in labels), key=lambda r: r[1])
    log("\n5 lowest-recall programmes:")
    for t, r, s in recalls[:5]:
        log(f"  {r:.4f}  (support {s})  {t}")

    pairs = sorted(((int(cm[i, j]), labels[i], labels[j]) for i in range(len(labels))
                    for j in range(len(labels)) if i != j and cm[i, j] > 0), key=lambda p: -p[0])
    log("\n10 most frequent confusion pairs (count | true -> predicted):")
    for c, a, b in pairs[:10]:
        log(f"  {c:3d} | {a} -> {b}")

    errors = int((np.asarray(y_test) != np.asarray(y_pred)).sum())
    same_field = int(sum(field_of(a) == field_of(b) for a, b in zip(np.asarray(y_test), np.asarray(y_pred)) if a != b))
    log(f"\nTotal errors: {errors} of {len(y_test)}")
    log(f"Errors within the same field (KUCCPS cluster number): {same_field} "
        f"({same_field / errors:.4f} of errors)" if errors else "Errors within the same field: 0")
    detail.update({
        "lowest_recall": [{"programme": t, "recall": r, "support": s} for t, r, s in recalls[:5]],
        "top_confusions": [{"true": a, "predicted": b, "count": c} for c, a, b in pairs[:10]],
        "total_errors": errors, "errors_same_field": same_field,
        "field_definition": "KUCCPS cluster number from the catalogue clusterGroup ('Cluster 6/7' counted as Cluster 6)",
        "classification_report": report, "confusion_matrix": cm.tolist(), "confusion_matrix_labels": labels,
    })
    metrics["xgboost_test_detail"] = detail

    # ---------------------------------------------------------------- figures
    log("\n=== Figures (training-split model) ===")
    figures = {}

    sample = df.sample(8, random_state=SEED)
    trait_cols = [c for c in numeric if c in TRAIT_COLUMN_INFO]
    table = pd.DataFrame({
        "Maths": sample["math_score"], "English": sample["eng_score"], "Chem.": sample["chem_score"],
        "Mean pts": sample["mean_points"],
        "Interests / strengths": sample[trait_cols].apply(
            lambda r: "; ".join(TRAIT_COLUMN_INFO[c][2] for c in trait_cols if r[c] == 1)[:70], axis=1),
        "Aspiration": sample["aspiration"].str.slice(0, 34),
        "Label": sample[TARGET].map(short).str.slice(0, 40),
    })
    fig, ax = plt.subplots(figsize=(13, 2.8))
    ax.axis("off")
    tbl = ax.table(cellText=table.values, colLabels=table.columns, loc="center", cellLoc="left")
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(6.5)
    tbl.auto_set_column_width(list(range(len(table.columns))))
    for (r, _), cell in tbl.get_celld().items():
        cell.set_edgecolor("#e4e3df")
        if r == 0:
            cell.set_text_props(weight="bold")
    ax.set_title("Sample of 8 rows from the v2 training dataset (selected columns; grade points 1-12)",
                 loc="left", fontsize=10)
    figures["dataset_sample"] = save(fig, "fig_dataset_sample.png")

    counts = y.value_counts().sort_values(ascending=False)
    figures["class_distribution"] = hbar(counts.values, [short(t) for t in counts.index], "Number of profiles",
                                         f"Profiles per programme (v2 dataset, {len(df)} rows, {len(counts)} classes)",
                                         "fig_class_distribution.png")

    names = list(models)
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), sharey=True)
    width = 0.26
    for ax, source, title in ((axes[0], "cv_train", "5-fold CV on training rows (mean, bar = std)"),
                              (axes[1], "test", "Held-out test rows (evaluated once)")):
        for k, (metric, label) in enumerate((("accuracy", "Accuracy"), ("macro_f1", "Macro-F1"),
                                             ("weighted_f1", "Weighted F1"))):
            if source == "cv_train":
                vals = [metrics[source][n][metric]["mean"] for n in names]
                err = [metrics[source][n][metric]["std"] for n in names]
            else:
                vals, err = [metrics[source][n][metric] for n in names], None
            ax.bar(np.arange(len(names)) + (k - 1) * width, vals, width - 0.03, yerr=err, color=SERIES[k],
                   label=label, error_kw={"ecolor": INK_2, "elinewidth": 0.8, "capsize": 2})
        ax.set_xticks(range(len(names)))
        ax.set_xticklabels([n.replace("Histogram Gradient Boosting", "Hist. Gradient\nBoosting")
                            .replace("Logistic Regression", "Logistic\nRegression")
                            .replace("Random Forest", "Random\nForest") for n in names])
        ax.set_ylim(0, 1)
        ax.set_title(title, loc="left", fontsize=10)
        ax.grid(axis="y", color="#e4e3df", linewidth=0.6)
        ax.set_axisbelow(True)
    axes[0].set_ylabel("Score")
    axes[0].legend(frameon=False, loc="lower left", ncol=3, fontsize=8)
    figures["model_comparison"] = save(fig, "fig_model_comparison.png")

    fnames = field_names()
    fields = sorted({field_of(t) for t in labels}, key=lambda f: int(f.split()[1]))
    fcm = confusion_matrix([field_of(t) for t in y_test], [field_of(t) for t in y_pred], labels=fields)
    figures["field_confusion_matrix"] = matrix_figure(
        fcm, [f"{f}: {fnames[f]}"[:42] for f in fields],
        "XGBoost test-set confusion by field (KUCCPS cluster), counts shown", "fig_confusion_field.png", 8.5, True)
    figures["full_confusion_matrix"] = matrix_figure(
        cm, [short(t)[:38] for t in labels], "XGBoost test-set confusion matrix, 53 programmes",
        "fig_confusion_full.png", 12, False)

    pre = xgb_pipe.named_steps["preprocessor"]
    feat_names = list(pre.get_feature_names_out())
    X_test_t = pre.transform(X_test)
    booster = xgb_pipe.named_steps["classifier"].clf_.get_booster()
    contribs = booster.predict(xgb.DMatrix(np.asarray(X_test_t, dtype=np.float32)), pred_contribs=True)
    contribs = np.abs(np.asarray(contribs)[:, :, :-1])  # rows x classes x features, bias dropped
    global_imp = contribs.mean(axis=(0, 1))
    order = np.argsort(-global_imp)[:15]
    figures["shap_global_top15"] = hbar(global_imp[order], [readable(feat_names[i]) for i in order],
                                        "Mean |SHAP value| (test rows, all programmes)",
                                        "Top 15 features overall (XGBoost, TreeSHAP)", "fig_shap_global_top15.png")
    ics_idx = list(xgb_pipe.classes_).index(ICS)
    ics_imp = contribs[:, ics_idx, :].mean(axis=0)
    order_ics = np.argsort(-ics_imp)[:15]
    figures["shap_ics_top15"] = hbar(ics_imp[order_ics], [readable(feat_names[i]) for i in order_ics],
                                     "Mean |SHAP value| for this programme's output (test rows)",
                                     "Top 15 features: BSc Informatics and Computer Science",
                                     "fig_shap_ics_top15.png")
    metrics["shap"] = {
        "method": "xgboost pred_contribs (TreeSHAP) on test rows; mean absolute value",
        "global_top15": [{"feature": feat_names[i], "label": readable(feat_names[i]), "mean_abs": float(global_imp[i])}
                         for i in order],
        "ics_top15": [{"feature": feat_names[i], "label": readable(feat_names[i]), "mean_abs": float(ics_imp[i])}
                      for i in order_ics],
    }
    metrics["figures"] = {k: os.path.relpath(v, ROOT) for k, v in figures.items()}

    # ------------------------------------------- old dataset, same protocol
    log("\n=== Same protocol on the OLD dataset (XGBoost, old features incl. skl_) ===")
    old = pd.read_csv(OLD_DATASET)
    o_num, o_cat = select_features(old, include_skills=True)
    o_feats = o_num + o_cat
    log(f"Old dataset: {OLD_DATASET}")
    log(f"Rows: {len(old)}  Classes: {old[TARGET].nunique()}  Features before one-hot: {len(o_feats)} "
        f"(skl_ columns: {sum(c.startswith('skl_') for c in o_feats)})")
    oX, oy = old[o_feats], old[TARGET]
    oX_tr, oX_te, oy_tr, oy_te = train_test_split(oX, oy, test_size=0.2, random_state=SEED, stratify=oy)
    log(f"Split sizes: train={len(oX_tr)}  test={len(oX_te)}")
    old_pipe = Pipeline([("preprocessor", preprocessor(o_num, o_cat)), ("classifier", make_xgb())])
    old_cv = cv_scores(clone(old_pipe), oX_tr, oy_tr)
    old_fit = clone(old_pipe).fit(oX_tr, oy_tr)
    old_test = test_scores(oy_te, old_fit.predict(oX_te))
    old_test["top3_accuracy"] = top_k_accuracy(old_fit, oX_te, oy_te, 3)
    new_cv = metrics["cv_train"]["XGBoost"]
    log(f"\n{'XGBoost':28s} {'OLD (with skills)':>18s} {'NEW (no skills)':>18s}")
    log(f"{'CV accuracy (train rows)':28s} {old_cv['accuracy']['mean']:>18.4f} {new_cv['accuracy']['mean']:>18.4f}")
    log(f"{'CV macro-F1 (train rows)':28s} {old_cv['macro_f1']['mean']:>18.4f} {new_cv['macro_f1']['mean']:>18.4f}")
    log(f"{'Test accuracy':28s} {old_test['accuracy']:>18.4f} {detail['accuracy']:>18.4f}")
    log(f"{'Test macro-F1':28s} {old_test['macro_f1']:>18.4f} {detail['macro_f1']:>18.4f}")
    log(f"{'Test top-3 accuracy':28s} {old_test['top3_accuracy']:>18.4f} {detail['top3_accuracy']:>18.4f}")
    metrics["old_dataset_comparison"] = {
        "path": os.path.relpath(OLD_DATASET, ROOT), "rows": len(old), "classes": int(oy.nunique()),
        "features_before_one_hot": len(o_feats), "cv_train": old_cv, "test": old_test,
    }

    with open(os.path.join(OUT_DIR, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)
    log(f"\nSaved metrics: {os.path.join(OUT_DIR, 'metrics.json')}")

    # ---------------------------------- deployment model (never used above)
    log("\n=== Deployment model: XGBoost refitted on ALL rows (not used for any reported number) ===")
    final = clone(models["XGBoost"]).fit(X, y)
    joblib.dump(final, MODEL_OUT, compress=("zlib", 3))
    log(f"Saved deployment model: {MODEL_OUT} ({os.path.getsize(MODEL_OUT) / 1024 / 1024:.2f} MB, "
        f"{len(final.classes_)} classes)")
    log(f"\nTotal time: {time.time() - started:.0f}s")


if __name__ == "__main__":
    deploy_only() if "--deploy-only" in sys.argv else main()
