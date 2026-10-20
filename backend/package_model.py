"""Prepares the trained model for publishing: compresses it and prints its SHA-256.

    python package_model.py

Reads rf_model_pipeline.pkl, writes model_release/rf_model_pipeline.pkl (about a tenth
of the size, identical predictions) and model_release/SHA256.txt. Upload the file to
the model host, then set MODEL_URL and MODEL_SHA256 on the server.
"""

import os

import joblib

from model_store import sha256_of

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "rf_model_pipeline.pkl")
OUT_DIR = os.path.join(HERE, "model_release")


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    target = os.path.join(OUT_DIR, "rf_model_pipeline.pkl")
    joblib.dump(joblib.load(SOURCE), target, compress=("zlib", 3))
    digest = sha256_of(target)
    with open(os.path.join(OUT_DIR, "SHA256.txt"), "w") as f:
        f.write(f"{digest}  rf_model_pipeline.pkl\n")
    print(f"{os.path.getsize(target) / 1e6:.0f} MB  sha256 {digest}")


if __name__ == "__main__":
    main()
