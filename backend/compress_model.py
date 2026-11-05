import os
import gc
import time
import hashlib
import joblib

os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

src = "rf_model_pipeline.pkl"
dst = "rf_model_pipeline_compressed.pkl"

orig_bytes = os.path.getsize(src)
print(f"Loading {src} ({orig_bytes / (1024*1024):.1f} MB)...")
t0 = time.time()
model = joblib.load(src)
print(f"Loaded into memory in {time.time() - t0:.1f}s.")

print("Compressing using ('zlib', 3)...")
t1 = time.time()
joblib.dump(model, dst, compress=("zlib", 3))
print(f"Compressed and saved in {time.time() - t1:.1f}s.")

del model
gc.collect()

comp_bytes = os.path.getsize(dst)
orig_mb = orig_bytes / (1024 * 1024)
comp_mb = comp_bytes / (1024 * 1024)
reduction = (1 - comp_bytes / orig_bytes) * 100

print(f"\nOriginal:   {orig_mb:.1f} MB")
print(f"Compressed: {comp_mb:.1f} MB")
print(f"Reduction:  {reduction:.1f}%")

h = hashlib.sha256()
with open(dst, "rb") as f:
    for chunk in iter(lambda: f.read(65536), b""):
        h.update(chunk)

print(f"\nNew SHA256: {h.hexdigest()}")
