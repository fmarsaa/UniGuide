"""Builds the figures and numbers used in Chapter 5 from the saved model and the Experiment 8 results.

Run from the repository root after run_comparison.py has finished:
    python ml/experiments/experiment_8_algorithm_comparison_current/make_evidence.py

Writes PNG figures and evidence.json into the figures/ folder next to this file.
Nothing here changes the deployed model or its metrics.
"""
import json
import os
import sys
import time

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import shap
from sklearn.model_selection import StratifiedKFold, cross_val_predict

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.abspath(os.path.join(HERE, "..", "..", "..", "backend"))
FIGS = os.path.join(HERE, "figures")
os.makedirs(FIGS, exist_ok=True)
sys.path.insert(0, BACKEND)
os.chdir(BACKEND)

from train_random_forest import DATASET_SIZE, FEATURE_COLUMNS, TARGET_COLUMN  # noqa: E402
from synthetic_data_generator import create_synthetic_dataset  # noqa: E402

ACCENT, GREY, DARK = "#2F5597", "#7F7F7F", "#222222"
plt.rcParams.update({"font.family": "serif", "font.size": 10, "axes.edgecolor": GREY, "axes.spines.top": False,
                     "axes.spines.right": False})


def save(fig, name):
    fig.savefig(os.path.join(FIGS, name), dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def short(title):
    return (title.replace("Bachelor of Science in ", "BSc ").replace("Bachelor of Arts in ", "BA ")
            .replace("Bachelor of Engineering in ", "BEng ").replace("Bachelor of ", "B. "))


evidence = {}
df = create_synthetic_dataset(DATASET_SIZE)
X, y = df[FEATURE_COLUMNS], df[TARGET_COLUMN]
metrics = json.load(open(os.path.join(BACKEND, "model_metrics.json")))

# ---- Figure: profiles per programme
counts = y.value_counts().sort_values()
fig, ax = plt.subplots(figsize=(6.4, 8.2))
ax.barh([short(t) for t in counts.index], counts.values, color=ACCENT)
ax.set_xlabel("Number of profiles")
ax.tick_params(axis="y", labelsize=6.5)
save(fig, "profiles_per_programme.png")
evidence["class_counts"] = {"min": int(counts.min()), "median": float(counts.median()), "max": int(counts.max())}

# ---- Figure: lowest per-programme F1
rep = metrics["classification_report"]
f1 = sorted(((k, v["f1-score"]) for k, v in rep.items() if isinstance(v, dict) and k not in ("macro avg", "weighted avg")), key=lambda r: r[1])
low = f1[:10][::-1]
fig, ax = plt.subplots(figsize=(6.4, 3.6))
ax.barh([short(k) for k, _ in low], [v for _, v in low], color=ACCENT)
ax.set_xlim(0, 1)
ax.set_xlabel("F1-score (out-of-fold)")
ax.axvline(metrics["weighted_f1"], color=GREY, linestyle="--", linewidth=1)
ax.tick_params(axis="y", labelsize=8)
save(fig, "lowest_f1.png")
evidence["f1_lowest"] = [(k, round(v, 3)) for k, v in f1[:10]]
evidence["f1_highest"] = [(k, round(v, 3)) for k, v in f1[-3:]]

# ---- most confused pairs
cm = np.array(metrics["confusion_matrix"])
labels = metrics["confusion_matrix_labels"]
pairs = sorted(((int(cm[i][j]), labels[i], labels[j]) for i in range(len(labels)) for j in range(len(labels)) if i != j and cm[i][j] > 0), reverse=True)
evidence["confused_pairs"] = pairs[:6]

# ---- Figure: algorithm comparison (Experiment 8)
res = json.load(open(os.path.join(HERE, "results.json")))
names = {"logistic_regression": "Logistic\nRegression", "random_forest": "Random\nForest", "gradient_boosting": "Gradient\nBoosting"}
rows = {}
for key in names:
    runs = res["runs"].get(key, [])
    if runs:
        a = [r["accuracy"] * 100 for r in runs]
        rows[key] = {"mean": float(np.mean(a)), "std": float(np.std(a)), "n": len(a), "weighted_f1": float(np.mean([r["weighted_f1"] * 100 for r in runs]))}
fig, ax = plt.subplots(figsize=(5.2, 3.4))
ax.bar([names[k] for k in rows], [rows[k]["mean"] for k in rows], yerr=[rows[k]["std"] for k in rows], capsize=4,
       color=[ACCENT if k == "random_forest" else "#A6A6A6" for k in rows])
for i, k in enumerate(rows):
    ax.text(i, rows[k]["mean"] + 0.6, "%.1f%%" % rows[k]["mean"], ha="center", fontsize=9)
ax.set_ylim(70, 92)
ax.set_ylabel("Accuracy (5-fold, mean of seeds)")
save(fig, "algorithm_comparison.png")
evidence["comparison"] = rows

# ---- pipeline diagram
fig, ax = plt.subplots(figsize=(8.4, 1.9))
ax.axis("off")
steps = ["Rule-based\nprofile generator", "Cleaning and\nchecks", "Train / holdout\nsplit (80/20)", "Random Forest\n(grid search, 5-fold)", "Evaluation\n(out-of-fold)", "Saved pipeline\n+ SHAP explainer"]
w, gap = 1.45, 0.22
for i, text in enumerate(steps):
    x = i * (w + gap)
    ax.add_patch(plt.Rectangle((x, 0.2), w, 0.8, fill=False, edgecolor=DARK, linewidth=1))
    ax.text(x + w / 2, 0.6, text, ha="center", va="center", fontsize=6.4)
    if i < len(steps) - 1:
        ax.annotate("", xy=(x + w + gap, 0.6), xytext=(x + w, 0.6), arrowprops=dict(arrowstyle="->", color=DARK))
ax.set_xlim(-0.1, len(steps) * (w + gap))
ax.set_ylim(0, 1.2)
save(fig, "pipeline.png")

# ---- out-of-fold top-1 and top-3 hit rate for all three models (the app shows three programmes)
pipe = joblib.load(os.path.join(BACKEND, "rf_model_pipeline.pkl"))
evidence["model_params"] = {k: str(v) for k, v in pipe.named_steps["classifier"].get_params().items() if k in ("n_estimators", "max_depth", "min_samples_leaf", "max_features", "class_weight", "random_state")}
sys.path.insert(0, HERE)
import run_comparison as rc  # noqa: E402

classes = np.array(sorted(y.unique()))
truth = np.searchsorted(classes, y.values)
evidence["top_k"] = {}
for name, make in rc.MODELS.items():
    t = time.time()
    oof = cross_val_predict(rc.build(make(42)), X, y, cv=StratifiedKFold(5, shuffle=True, random_state=42), method="predict_proba", n_jobs=1)
    order = np.argsort(-oof, axis=1)[:, :3]
    evidence["top_k"][name] = {"top1": float((order[:, 0] == truth).mean()),
                               "top3": float(np.mean([truth[i] in order[i] for i in range(len(truth))]))}
    print(name, evidence["top_k"][name], "%.0fs" % (time.time() - t), flush=True)

# ---- SHAP global importance (same approximate method the app uses), career columns merged into one
sample = X.sample(400, random_state=7)
pre = pipe.named_steps["preprocessor"]
Xt = pre.transform(sample)
names_out = pre.get_feature_names_out()
explainer = shap.TreeExplainer(pipe.named_steps["classifier"])
sv = explainer.shap_values(Xt, check_additivity=False, approximate=True)
sv = np.array(sv)  # (samples, features, classes) or (classes, samples, features)
if sv.shape[0] != len(sample):
    sv = np.moveaxis(sv, 0, -1)
imp = np.abs(sv).mean(axis=(0, 2))
merged = {}
for n, v in zip(names_out, imp):
    label = "Career choice" if n.startswith("cat__aspiration") else n.split("__", 1)[1]
    merged[label] = merged.get(label, 0) + float(v)
try:
    from synthetic_data_generator import TRAIT_COLUMN_INFO
    pretty = {c: "%s: %s" % (info[1], info[2]) for c, info in TRAIT_COLUMN_INFO.items()}
except Exception:
    pretty = {}
pretty.update({"math_score": "Mathematics grade", "eng_score": "English grade", "kis_score": "Kiswahili grade", "chem_score": "Chemistry grade",
               "bio_score": "Biology grade", "phys_score": "Physics grade", "mean_points": "KCSE mean points"})
top = sorted(merged.items(), key=lambda kv: kv[1])[-12:]
fig, ax = plt.subplots(figsize=(6.4, 4.2))
ax.barh([pretty.get(k, k) for k, _ in top], [v for _, v in top], color=ACCENT)
ax.set_xlabel("Mean absolute SHAP value (all programmes)")
ax.tick_params(axis="y", labelsize=8)
save(fig, "shap_global.png")
evidence["shap_top"] = [(pretty.get(k, k), round(v, 4)) for k, v in top[::-1]]

# ---- sample of dataset rows for the dataset table
cols = ["math_score", "eng_score", "kis_score", "chem_score", "bio_score", "phys_score", "mean_points", "aspiration", TARGET_COLUMN]
evidence["sample_rows"] = df[cols].head(5).to_dict(orient="records")
evidence["dataset"] = {"rows": len(df), "classes": int(y.nunique()), "features": len(FEATURE_COLUMNS) + 0}

json.dump(evidence, open(os.path.join(FIGS, "evidence.json"), "w"), indent=2, default=str)
print(json.dumps({k: evidence[k] for k in ("top_k", "comparison", "shap_top")}, indent=1, default=str))
