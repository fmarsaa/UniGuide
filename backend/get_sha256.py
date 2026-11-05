import hashlib
path = "rf_model_pipeline.pkl"
h = hashlib.sha256()
with open(path, "rb") as f:
    for chunk in iter(lambda: f.read(65536), b""):
        h.update(chunk)
print("SHA256:", h.hexdigest())
print("File size (MB):", round(__import__("os").path.getsize(path) / 1024 / 1024, 2))
