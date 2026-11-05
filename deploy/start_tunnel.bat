@echo off
REM Serves the backend to the internet from this laptop through an ngrok tunnel, so students can use the phone app anywhere.
REM Usage:  deploy\start_tunnel.bat [your-free-domain.ngrok-free.app]
REM With no domain, ngrok gives a new random address every time (the phone app would then need rebuilding each time).
REM The laptop must stay on, awake and online while students use the app. Close Chrome and the emulator first.

set DOMAIN=%1

echo [1/3] Starting the backend (about 30 seconds to load the model)...
start "UniGuide backend" cmd /k "cd /d %~dp0..\backend && python -m uvicorn main:app --host 127.0.0.1 --port 8000"

:waitbackend
timeout /t 4 /nobreak >nul
curl -s -o nul -w "%%{http_code}" http://127.0.0.1:8000/api/health | find "200" >nul
if errorlevel 1 goto waitbackend
echo Backend is ready.

echo [2/3] Starting the tunnel...
if "%DOMAIN%"=="" (
  start "UniGuide tunnel" cmd /k "ngrok http 8000"
) else (
  start "UniGuide tunnel" cmd /k "ngrok http --url=%DOMAIN% 8000"
)

timeout /t 6 /nobreak >nul
echo [3/3] Your public address:
powershell -NoProfile -Command "(Invoke-RestMethod http://127.0.0.1:4040/api/tunnels).tunnels[0].public_url"
echo.
echo Open that address followed by /api/health in a browser to check it. Keep both windows open.
pause
