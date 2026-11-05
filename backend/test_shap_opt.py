import joblib
import psutil

pipeline = joblib.load("rf_model_pipeline_pruned.pkl")
clf = pipeline.named_steps["classifier"]

proc = psutil.Process()
print(f"RAM before: {proc.memory_info().rss / 1024 / 1024:.1f} MB")

# Test if creating TreeExplainer with model_output='probability' or subset of trees
import shap
explainer = shap.TreeExplainer(clf, feature_perturbation="tree_path_dependent")
print(f"RAM after: {proc.memory_info().rss / 1024 / 1024:.1f} MB")
