@echo off
REM UniGuide web admin portal launcher.
REM Needs only the backend and a browser - no Android emulator, so it also uses far less memory.
REM The portal must run on port 5000: that is the address the server allows (see CORS_ORIGINS in backend/main.py).
REM First-time setup: flutter_app\web_firebase.json must exist (see the "Admin web portal" section of README.md).

echo [1/2] Starting the backend (takes about 30 seconds to load the model)...
start "UniGuide backend" cmd /k "cd /d %~dp0backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000"

:waitbackend
timeout /t 4 /nobreak >nul
curl -s -o nul -w "%%{http_code}" http://127.0.0.1:8000/api/health | find "200" >nul
if errorlevel 1 goto waitbackend
echo Backend is ready.

echo [2/2] Opening the admin portal in Chrome...
cd /d %~dp0flutter_app
flutter run -d chrome --web-port 5000 --dart-define-from-file=web_firebase.json
