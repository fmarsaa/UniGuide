# UniGuide Backend: FastAPI & Random Forest ML Subsystem

**Project Title**: UniGuide: A Random Forest-Based Decision Support System for University Degree Programme Recommendation Among Kenyan Form-Four Leavers  
**Student**: Fatuma Omar Marsa (Admission No: 159056, Class: ICS 4A)  
**Supervisor**: Deperias Webula Kerre  
**Institution**: Strathmore University, School of Computing and Engineering Sciences  

---

## Technical Specifications (Proposal Chapter 3 & 4)

- **Language**: Python 3.10+
- **Framework**: FastAPI (Asynchronous REST API)
- **Machine Learning**: Scikit-Learn `RandomForestClassifier` (150 estimators, max depth 12)
- **Explainability**: SHAP (SHapley Additive exPlanations) `TreeExplainer`
- **Data Generation**: Large Language Model / Heuristic synthetic student profile generator (N=1,500 validated profiles)
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
- Generates 1,500 synthetic Kenyan student profiles.
- Executes an 80/20 stratified train-test split.
- Performs one-hot encoding for interests, skills, strengths, and aspirations.
- Trains the Random Forest ensemble and outputs the Classification Report (Accuracy, Precision, Recall, Weighted F1).
- Initializes the SHAP TreeExplainer and serializes the model pipeline to `rf_model_pipeline.pkl`.

### 3. Start the FastAPI REST Server
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Interactive Swagger Documentation
Open your browser at:
`http://localhost:8000/docs` to test `/api/recommend` and `/api/feedback`.
