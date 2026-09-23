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

## Technology Stack

- **Mobile App**: Flutter (Dart), Material 3 — see [flutter_app/](flutter_app)
- **Backend**: FastAPI (Python) REST API — see [backend/](backend)
- **Machine Learning**: Scikit-Learn Random Forest classifier, SHAP (TreeExplainer) for explainability
- **Data & Auth**: Firebase Authentication and Cloud Firestore

## Project Structure

- `flutter_app/` — Flutter mobile client (student & admin screens, wireframes from proposal Figures 4.6–4.11)
- `backend/` — FastAPI service, synthetic dataset generator, and Random Forest training pipeline
- `firestore.rules`, `firebase-blueprint.json` — Firestore security rules and data schema
