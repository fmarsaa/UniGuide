"""Builds the folder to upload to a Hugging Face Docker Space (the hosted backend).

    python deploy/make_space_bundle.py

Creates deploy/space_bundle/ holding the backend code, pinned requirements, the XGBoost model
(uniguide_xgb_v4.joblib, trained without student skills), its metrics summary,
Dockerfile, and the Space's README.md with Hugging Face YAML metadata.
"""
import glob
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(HERE, "..", "backend")
OUT = os.path.join(HERE, "space_bundle")

README = """---
title: UniGuide API
emoji: 🎓
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# UniGuide Backend API

Backend for UniGuide, a decision support system that recommends university degree programmes to Kenyan Form Four leavers.
Interactive API documentation is available at `/docs` once the Space is running.
"""


def main() -> None:
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)

    for path in glob.glob(os.path.join(BACKEND, "*.py")):
        shutil.copy(path, OUT)

    shutil.copy(os.path.join(BACKEND, "requirements.txt"), OUT)

    model_path = os.path.join(BACKEND, "uniguide_xgb_v4.joblib")
    if not os.path.isfile(model_path):
        raise SystemExit(f"Model not found: {model_path}. Run backend/train_evaluate.py first.")
    shutil.copy(model_path, OUT)
    print(f"Copied XGBoost model uniguide_xgb_v4.joblib ({os.path.getsize(model_path)/(1024*1024):.2f} MB)")

    metrics = os.path.join(BACKEND, "model_metrics_v4.json")
    if os.path.isfile(metrics):
        shutil.copy(metrics, OUT)
        print("Copied model_metrics_v4.json")
    else:
        print("model_metrics_v4.json not found; the backend will report the version as xgb-v4-<date>")

    dockerfile = open(os.path.join(BACKEND, "Dockerfile"), encoding="utf-8").read()
    with open(os.path.join(OUT, "Dockerfile"), "w", encoding="utf-8", newline="\n") as f:
        f.write(dockerfile)

    with open(os.path.join(OUT, "README.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(README)

    banned = [n for n in os.listdir(OUT) if n.endswith(".env") or "serviceAccount" in n or "firebase-adminsdk" in n]
    assert not banned, banned
    models = sorted(n for n in os.listdir(OUT) if n.endswith((".pkl", ".joblib")))
    assert models == ["uniguide_xgb_v4.joblib"], models
    print(f"Model files in bundle: {models}")
    print(f"{len(os.listdir(OUT))} files written to {os.path.abspath(OUT)}:")
    for name in sorted(os.listdir(OUT)):
        print(f"  {name}")


if __name__ == "__main__":
    main()
