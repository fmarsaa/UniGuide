# UniGuide Mobile: Flutter Android Application

**Project Title**: UniGuide: A Random Forest-Based Decision Support System for University Degree Programme Recommendation Among Kenyan Form-Four Leavers  
**Student**: Fatuma Omar Marsa (Admission No: 159056, Class: ICS 4A)  
**Supervisor**: Deperias Webula Kerre  
**Institution**: Strathmore University, School of Computing and Engineering Sciences  

---

## Architecture Implemented (Proposal Section 4)

1. **Frontend**: Native Flutter (Dart) targeting Android mobile OS with Material 3 design.
2. **Wireframe Realization**:
   - **Figure 4.6 (Authentication Wireframe)**: `lib/screens/auth_screen.dart` (Student / Admin role-based login and registration).
   - **Figure 4.7 (Profile Setup Wireframe)**: `lib/screens/profile_setup_screen.dart` (KCSE subject grades, academic interests, skills, strengths, and career aspirations).
   - **Figure 4.8 (Recommendation Wireframe)**: `lib/screens/recommendations_screen.dart` (Top 3 ranked degree courses with prediction confidence %, SHAP feature attribution weights, KUCCPS cutoff status).
   - **Figure 4.9 (Programme Information Wireframe)**: `lib/screens/programme_detail_screen.dart` (Admission prerequisites, cluster point history, offering universities, career pathways, certifications).
   - **Figure 4.10 (Admin Dashboard Wireframe)**: `lib/screens/admin_dashboard_screen.dart` (Manage degree cutoffs, CUE accreditations, audit trails).
   - **Figure 4.11 (Rating & Feedback Wireframe)**: `lib/screens/feedback_dialog.dart` (5-star usability rating and qualitative review persisted to Cloud Firestore).
3. **Machine Learning Model**: Scikit-Learn `RandomForestClassifier` with `shap.TreeExplainer`.
4. **Backend**: FastAPI (`/backend`) providing REST endpoints.

---

## How to Run on Android Studio / Flutter CLI

### 1. Prerequisites
- Flutter SDK (version >= 3.0.0)
- Android Studio with Android SDK (API 33+) or VS Code with Flutter Extension
- Android Device or Android Virtual Device (AVD) emulator running

### 2. Install Dependencies
```bash
cd flutter_app
flutter pub get
```

### 3. Launch on Connected Android Device or Emulator
```bash
flutter run
```

To target a specific Android device:
```bash
flutter devices
flutter run -d <device_id>
```

### 4. Build Android Release APK
```bash
flutter build apk --release
# The APK will be generated at build/app/outputs/flutter-apk/app-release.apk
```
