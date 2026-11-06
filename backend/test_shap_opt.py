import joblib
import psutil

pipeline = joblib.load("uniguide_xgb_v4.joblib")
clf = pipeline.named_steps["classifier"]
clf = getattr(clf, "clf_", clf)  # the XGBoost model inside the string-label wrapper

proc = psutil.Process()
print(f"RAM before: {proc.memory_info().rss / 1024 / 1024:.1f} MB")

# Test if creating TreeExplainer with model_output='probability' or subset of trees
import shap
explainer = shap.TreeExplainer(clf, feature_perturbation="tree_path_dependent")
print(f"RAM after: {proc.memory_info().rss / 1024 / 1024:.1f} MB")
