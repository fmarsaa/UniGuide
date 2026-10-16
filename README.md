# UniGuide

A Random Forest-Based Decision Support System for University Degree Programme Recommendation Among Kenyan Form-Four Leavers.

**Author**: Fatuma Omar Marsa  


## Features

- **Student KCSE Profile Setup**: Capture KCSE mean grade, subject cluster grades, interests, skills, strengths, and career aspirations.
- **Random Forest Recommendation Engine**: Computes multi-attribute compatibility scores based on prerequisite admission criteria, subject strength, and personal career attributes.
- **Explainable AI (SHAP TreeExplainer Analysis)**: Visualizes exact mathematical feature contributions behind each recommendation.
- **Kenyan Universities & Programmes Directory**: Detailed curriculum overviews, historical KUCCPS cutoff points, accredited universities (e.g. Strathmore University, University of Nairobi, JKUAT, Kenyatta University, Moi University), recommended skills, and industry certifications.
- **Form-Four Leaver Evaluation Feedback**: Star rating system and comments, persisted to Cloud Firestore.

## Getting Started

1. Train the Random Forest model and start the backend: [backend/README.md](backend/README.md)
2. Configure Firebase and run the mobile app: [flutter_app/README.md](flutter_app/README.md)

Both `/api/recommend` and Firebase sign-in are real - there is no offline demo
mode with fabricated predictions or credentials, so the backend and a
configured Firebase project are required for the app to do anything.

## Admin web portal

Administrators can use UniGuide from a web browser as well as from the phone app. The portal is the same Flutter code built for the web, and it talks to the same protected admin endpoints, so there is no second backend or second sign-in. Students who sign in on the web are told to use the phone app.

One-time setup:

1. Register a web app in the Firebase project (`firebase apps:create web "UniGuide Admin Portal" --project <project-id>`).
2. Save its settings (`firebase apps:sdkconfig WEB <app-id> --project <project-id>`) into `flutter_app/web_firebase.json` as `FIREBASE_API_KEY`, `FIREBASE_AUTH_DOMAIN`, `FIREBASE_PROJECT_ID`, `FIREBASE_STORAGE_BUCKET`, `FIREBASE_MESSAGING_SENDER_ID` and `FIREBASE_APP_ID`. This file is git-ignored, like `google-services.json`.

Run it with `start_admin_portal.bat`, or manually: start the backend, then `flutter run -d chrome --web-port 5000 --dart-define-from-file=web_firebase.json` from `flutter_app/`. The backend only accepts browser requests from `http://localhost:5000` by default; set `CORS_ORIGINS` in `backend/.env` (comma-separated) if the portal is hosted elsewhere.

## Technology Stack

- **Mobile App**: Flutter (Dart), Material 3 — see [flutter_app/](flutter_app)
- **Backend**: FastAPI (Python) REST API — see [backend/](backend)
- **Machine Learning**: Scikit-Learn Random Forest classifier, SHAP (TreeExplainer) for explainability
- **Data & Auth**: Firebase Authentication and Cloud Firestore

## Project Structure

- `flutter_app/` — Flutter mobile client (student & admin screens, wireframes from proposal Figures 4.6–4.11)
- `backend/` — FastAPI service, synthetic dataset generator, and Random Forest training pipeline
- `firestore.rules`, `firebase-blueprint.json` — Firestore security rules and data schema
