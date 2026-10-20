# UniGuide

A Random Forest-based decision support system that recommends university degree programmes to Kenyan Form Four leavers and explains each recommendation in plain language.

**Author**: Fatuma Omar Marsa (159056), Strathmore University, supervised by Deperias Webula Kerre

## What it does

- **Student app (Android, Flutter)**: sign in with a verified email, enter KCSE grades, interests, skills and strengths (the career step is optional), and get three programmes with reasons. Students can save and compare programmes, try different grades in a what-if screen, download a PDF report, rate the result, and delete their account and data. An optional fingerprint or face unlock protects the app.
- **Recommendation engine (FastAPI)**: a Random Forest scores 53 programmes, the KUCCPS minimum subject grades remove programmes the student cannot enter, and each university's own latest cutoff is compared with the student's cluster points. SHAP supplies the reasons.
- **Administrator web portal (same Flutter code, built for the browser)**: insights charts, per-university cutoffs, feedback, administrators, model retrain and restore, a weekly catalogue check against KUCCPS, and an audit log.
- **Data and sign-in**: Firebase Authentication and Cloud Firestore. The apps never read Firestore directly; every request goes through the backend.

## Run it locally

1. Backend: see [backend/README.md](backend/README.md) (install, train the model, start the server).
2. Phone app: see [flutter_app/README.md](flutter_app/README.md).
3. Admin web portal: `start_admin_portal.bat`, or start the backend and run `flutter run -d chrome --web-port 5000 --dart-define-from-file=web_firebase.json` in `flutter_app/`. The Firebase web settings go in `flutter_app/web_firebase.json` (git-ignored); register the web app once with `firebase apps:create web`. The backend accepts browser requests from `http://localhost:5000` by default; set `CORS_ORIGINS` in `backend/.env` if the portal is hosted elsewhere.

There is no demo mode with made-up predictions: the backend and a configured Firebase project are required.

## Tests

```bash
cd backend && pip install -r requirements-dev.txt && python -m pytest -q
cd flutter_app && flutter test
```

The backend tests that need the trained model are skipped when the model file is absent. GitHub Actions runs both suites on every push (`.github/workflows/tests.yml`).

## Release and deployment

- `backend/Dockerfile` packages the backend. The trained model, the Firebase key and `.env` are never put in the image.
- The trained model (2.27 GB; 234 MB compressed with identical predictions) is not in git. `python backend/package_model.py` compresses it and prints its SHA-256. Publish the file, then set `MODEL_URL` and `MODEL_SHA256` on the server: it downloads the model once and refuses a file that does not match.
- Settings are listed in [backend/.env.example](backend/.env.example). On a host that keeps secrets as environment variables, put the Firebase key's JSON in `FIREBASE_SERVICE_ACCOUNT_JSON`.
- The system has been run locally only; it has not been deployed to a public HTTPS address.

## Project structure

- `flutter_app/`: Flutter client (student screens, administrator portal)
- `backend/`: FastAPI service, synthetic data generator, training script, tests
- `ml/experiments/`: every experiment with its README and results, including the algorithm comparison (Experiment 8) and the tool for the student sessions
- `catalogue_verification/`: scripts and report that checked the programme catalogue against the KUCCPS cutoff list
- `firestore.rules`, `firebase-blueprint.json`: Firestore rules (clients are denied direct access) and data schema

## Known limitations

- The training labels come from a rule written for this project, so reported accuracy shows how well the model reproduces that rule, not how often it matches a real student's best programme.
- 53 of about 460 KUCCPS degrees are covered, and each programme lists one to four universities. Three cutoffs are unverified.
- Gradient Boosting and Logistic Regression scored higher than the Random Forest on this data (Experiment 8); the Random Forest was kept because the proposal names it.
