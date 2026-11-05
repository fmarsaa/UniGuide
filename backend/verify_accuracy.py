import joblib
import numpy as np
from synthetic_data_generator import create_synthetic_dataset
from train_random_forest import FEATURE_COLUMNS, TARGET_COLUMN
from sklearn.metrics import accuracy_score, f1_score

print("Generating 1,000 holdout test students...")
test_df = create_synthetic_dataset(1000)
X = test_df[FEATURE_COLUMNS]
y = test_df[TARGET_COLUMN]

print("Evaluating original 350-tree model...")
orig_pipeline = joblib.load("rf_model_pipeline.pkl")
y_pred_orig = orig_pipeline.predict(X)
acc_orig = accuracy_score(y, y_pred_orig)
f1_orig = f1_score(y, y_pred_orig, average="weighted")

print("Evaluating pruned 60-tree model...")
pruned_pipeline = joblib.load("rf_model_pipeline_pruned.pkl")
y_pred_pruned = pruned_pipeline.predict(X)
acc_pruned = accuracy_score(y, y_pred_pruned)
f1_pruned = f1_score(y, y_pred_pruned, average="weighted")

# Also measure agreement between the two models
agreement = np.mean(y_pred_orig == y_pred_pruned) * 100

print("\n" + "="*50)
print(f"Original Model (350 trees): Accuracy = {acc_orig*100:.2f}%, Weighted F1 = {f1_orig*100:.2f}%")
print(f"Pruned Model   ( 60 trees): Accuracy = {acc_pruned*100:.2f}%, Weighted F1 = {f1_pruned*100:.2f}%")
print(f"Difference in Accuracy:     {abs(acc_orig - acc_pruned)*100:+.2f}%")
print(f"Direct Agreement Rate:      {agreement:.2f}%")
print("="*50)
