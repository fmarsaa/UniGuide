# Hosting UniGuide

Backend on a Hugging Face Docker Space, admin portal on Cloudflare Pages, phone app as a release APK that points to the hosted backend.
Both services have free tiers that do not ask for a card; check the current limits before relying on them.

## 1. Prepare the files (on your laptop)

```bash
python backend/package_model.py          # writes backend/model_release/ (234 MB model + SHA256.txt)
python deploy/make_space_bundle.py       # writes deploy/space_bundle/ (code, Dockerfile, README)
```

## 2. Put the model on Hugging Face

1. Create a **model repository** (private is fine), e.g. `uniguide-model`.
2. Upload `backend/model_release/rf_model_pipeline.pkl` through the website (Files, Add file, Upload).
3. Its address is `https://huggingface.co/<you>/uniguide-model/resolve/main/rf_model_pipeline.pkl`.
4. Create a **read token** (Settings, Access Tokens, type Read) if the repository is private.

## 3. Create the backend Space

1. New Space, SDK **Docker**, blank template, hardware **CPU basic (free)**.
2. Upload everything inside `deploy/space_bundle/` to the Space (website upload, or `git push` to the Space repository).
3. In the Space, Settings, **Variables and secrets**, add:

| Name | Type | Value |
|---|---|---|
| `FIREBASE_SERVICE_ACCOUNT_JSON` | Secret | the whole content of `serviceAccountKey.json` |
| `ADMIN_EMAILS` | Variable | your administrator email |
| `MODEL_URL` | Variable | the address from step 2 |
| `MODEL_SHA256` | Variable | the value in `backend/model_release/SHA256.txt` |
| `MODEL_TOKEN` | Secret | the read token (only if the model repository is private) |
| `CORS_ORIGINS` | Variable | your portal address from step 4 (add it after step 4) |

4. The Space builds, downloads the model, and starts. Open `https://<you>-<space>.hf.space/api/health`: it should say `"model_loaded": true`.

Free Spaces go to sleep when idle, so open the health address a minute before a demo.

## 4. Admin portal on Cloudflare Pages

Cloudflare cannot build Flutter, so build it on your laptop and upload the result:

```bash
cd flutter_app
flutter build web --release --dart-define-from-file=web_firebase.json --dart-define=API_BASE_URL=https://<you>-<space>.hf.space
```

1. Cloudflare dashboard, Workers and Pages, Create, Pages, **Upload assets**.
2. Upload the folder `flutter_app/build/web`. You get an address like `https://uniguide-admin.pages.dev`.
3. Put that address in the Space's `CORS_ORIGINS` (no trailing slash) and let the Space restart.
4. Firebase console, Authentication, Settings, **Authorized domains**, add `uniguide-admin.pages.dev`.

## 5. Phone app

```bash
cd flutter_app
flutter build apk --release --dart-define=API_BASE_URL=https://<you>-<space>.hf.space
```

The APK is in `flutter_app/build/app/outputs/flutter-apk/app-release.apk`. Send it by a Drive link. Students then use the app from anywhere, with no laptop needed.

## 6. Check it

- Health address says the model is loaded and Firestore is configured.
- Sign in to the portal at the Pages address; the Insights page loads.
- Install the APK, register, get recommendations.
- Record the three addresses, the commit and the model version for the report (Section 5.2.3 then needs rewriting from "not deployed").
