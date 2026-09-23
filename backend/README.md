# UniGuide Backend: FastAPI & Random Forest ML Subsystem

**Project Title**: UniGuide: A Random Forest-Based Decision Support System for University Degree Programme Recommendation Among Kenyan Form-Four Leavers  
**Student**: Fatuma Omar Marsa (Admission No: 159056, Class: ICS 4A)  
**Supervisor**: Deperias Webula Kerre  
**Institution**: Strathmore University, School of Computing and Engineering Sciences  

---

## Technical Specifications (Proposal Chapter 3 & 4)

- **Language**: Python 3.10+
- **Framework**: FastAPI (Asynchronous REST API)
- **Machine Learning**: Scikit-Learn `RandomForestClassifier`, hyperparameters chosen by grid search (see `model_metrics.json` after training)
- **Explainability**: SHAP (SHapley Additive exPlanations) `TreeExplainer`
- **Data Generation**: Deterministic rule-based synthetic student profile generator (N=3,000 seeded/reproducible profiles), each with 7-9 KCSE subjects (5 compulsory + 2-4 optional from the full KNEC list, matching real candidates - see `kuccps.py`)
- **Database Connection**: Firebase Authentication & Cloud Firestore

---

## Setup & Running Instructions

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Generate Dataset & Train the Random Forest Model
```bash
python train_random_forest.py
```
This runs the full CRISP-DM training pipeline:
- Generates 3,000 synthetic Kenyan student profiles (seeded, so re-running
  produces the same dataset), labelled by a deterministic rule (KUCCPS
  eligibility gate, then interest/skill/aspiration matching against
  `programmes_catalog.py`, tie-broken by closeness to each programme's cutoff).
- Executes an 80/20 stratified train-test split.
- Performs one-hot encoding for interests, skills, strengths, and aspirations.
- Grid-searches Random Forest hyperparameters with 5-fold cross-validation
  (weighted F1), using balanced class weights to compensate for programmes
  like Medicine that have far fewer eligible synthetic profiles than others.
- Refits the best pipeline and writes the Classification Report (Accuracy,
  Precision, Recall, Weighted F1, confusion matrix, chosen hyperparameters)
  to `model_metrics.json`.
- Serializes the fitted pipeline to `rf_model_pipeline.pkl`, loaded directly by
  `main.py` at inference time (no logic is duplicated between training and serving).

Latest run: **74.5% accuracy / 72.5% weighted F1** on held-out test data. Some
programmes remain harder to separate than others - Software Engineering vs.
Informatics and Computer Science share nearly identical KUCCPS requirements and
a combined "Software Engineer / AI Architect" aspiration option in the app, so
the model has genuinely little signal to tell them apart. Worth naming as a
limitation in your evaluation chapter rather than a bug to chase further.

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
