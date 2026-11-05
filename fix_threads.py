with open('backend/train_xgboost.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('N_JOBS = int(os.environ.get("TRAIN_N_JOBS", "4"))', 'N_JOBS = 1')
text = text.replace('n_jobs=4, random_state=42):', 'n_jobs=2, random_state=42):')
text = text.replace('n_jobs=N_JOBS,', 'n_jobs=1,')

with open('backend/train_xgboost.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("UPDATED THREAD CONFIG")
