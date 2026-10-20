# UniGuide Backend: FastAPI & Random Forest ML Subsystem

**Project Title**: UniGuide: A Random Forest-Based Decision Support System for University Degree Programme Recommendation Among Kenyan Form-Four Leavers  
**Student**: Fatuma Omar Marsa (Admission No: 159056, Class: ICS 4A)  
**Supervisor**: Deperias Webula Kerre  
**Institution**: Strathmore University, School of Computing and Engineering Sciences  

---

## Technical Specifications

- **Language**: Python 3.12 (dependencies are pinned in `requirements.txt`; `requirements-dev.txt` adds the test tools)
- **Framework**: FastAPI
- **Machine learning**: scikit-learn `RandomForestClassifier` inside a pipeline, hyperparameters chosen by grid search
- **Explainability**: SHAP `TreeExplainer` (approximate mode, so a request takes milliseconds rather than half a minute)
- **Data generation**: a seeded, rule-based generator (`synthetic_data_generator.py`) that produces 15,322 profiles over 53 programmes; the same seed gives the same data
- **Database and sign-in**: Firebase Authentication and Cloud Firestore, reached only through this backend

---

## Setup & Running Instructions

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements-dev.txt
```

### 2. Train the Random Forest Model
```bash
python train_random_forest.py
```
This generates the dataset, holds out 20% for a reference check, grid-searches the Random Forest with 5-fold
cross-validation on the training split, evaluates with 5-fold out-of-fold predictions over all profiles, refits on
the full data, and writes:

- `rf_model_pipeline.pkl`: the fitted pipeline (compressed with joblib; about a tenth of the plain pickle)
- `model_metrics.json`: accuracy, F1, per-programme report, confusion matrix, chosen settings, and a run record
  (git commit, dataset fingerprint, seeds, library versions, model version)

The previous model is backed up to `model_backups/` before it is replaced. Latest run: 80.85% accuracy and 80.68%
weighted F1 out of fold; 81.14% and 80.98% on the held-out 20%. See `ml/experiments/` for every experiment, including
the comparison with Logistic Regression and Gradient Boosting.

### 2b. Run the tests
```bash
python -m pytest -q
```
Tests that need the trained model are skipped when `rf_model_pipeline.pkl` is absent.

### 2c. A server without the model file
Run `python package_model.py` to compress the model and print its SHA-256, publish the file, and set `MODEL_URL`
and `MODEL_SHA256` on the server (see `.env.example`). It downloads the file once and refuses one that does not match.
A `Dockerfile` is included; the model, the Firebase key and `.env` are not copied into the image.

### 3. Configure Firebase (required for auth + persistence)
`/api/recommend`, `/api/feedback`, `/api/auth/whoami`, and the admin endpoint all
verify a Firebase Auth ID token and read/write Cloud Firestore via the Admin SDK,
per the proposal's architecture (IR-05). Without this configured, the server still
starts and `/api/programmes` still works, but those endpoints return `503` rather
than silently faking success.

1. Firebase Console → Project Settings → Service Accounts → **Generate new private key**.
2. Save the JSON file somewhere outside version control, e.g. `backend/serviceAccountKey.json`
   (already covered by `.gitignore`).
3. Copy `.env.example` to `.env` and set `FIREBASE_SERVICE_ACCOUNT_PATH` to that file's path.
4. Set `ADMIN_EMAILS` to a comma-separated allowlist of accounts that should be
   granted the administrator role the first time they sign in.

### 4. Start the FastAPI REST Server
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. HTTPS (proposal IR-06)
Running `uvicorn` directly serves plain HTTP, which is fine for local development
against an emulator or a phone on the same LAN. IR-06 requires HTTPS between the
app and backend for any deployment reachable over the open internet. This needs
a real domain name and certificate, which can't be generated for you - pick one:

- **Quick demo (no domain needed)**: `ngrok http 8000` gives you a temporary
  `https://...ngrok-free.app` URL that tunnels to your local server. Pass it to
  the app with `flutter run --dart-define=API_BASE_URL=https://<your-ngrok-url>`.
- **Real deployment**: host `main.py` behind a reverse proxy that terminates
  TLS (Caddy auto-provisions Let's Encrypt certificates with zero config), or
  deploy to a PaaS that gives you HTTPS automatically (Render, Railway, Fly.io).
  Either way, `uvicorn` keeps listening on plain HTTP behind the proxy.

### 6. Interactive Swagger Documentation
Open your browser at:
`http://localhost:8000/docs` to test `/api/recommend`, `/api/feedback`, `/api/auth/whoami`,
`/api/programmes`, and `/api/admin/programmes/{id}`. Authenticated routes expect an
`Authorization: Bearer <Firebase ID token>` header, which the Flutter app attaches
automatically once signed in.
