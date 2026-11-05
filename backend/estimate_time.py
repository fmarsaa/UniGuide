from synthetic_data_generator import create_synthetic_dataset
import time
t = time.time()
df = create_synthetic_dataset(100)
elapsed = time.time() - t
print(f"100 rows in {elapsed:.2f} sec")
print(f"Estimated full 15000 rows: {elapsed * 150 / 60:.1f} min (data gen only)")
print(f"Rows generated: {len(df)}")
