@echo off
REM UniGuide demo launcher - starts everything in the order that fits in 7.5 GB of RAM.
REM Before running: close Chrome and any other heavy programs.

echo [1/3] Starting the Android emulator (takes about 2 minutes)...
start "" "%LOCALAPPDATA%\Android\Sdk\emulator\emulator.exe" -avd Medium_Phone_API_36.0 -no-snapshot-load -no-boot-anim

:waitboot
timeout /t 8 /nobreak >nul
adb reconnect >nul 2>&1
for /f "delims=" %%b in ('adb -s emulator-5554 shell getprop sys.boot_completed 2^>nul') do set BOOTED=%%b
if not "%BOOTED:~0,1%"=="1" goto waitboot
echo Emulator is ready.

echo [2/3] Starting the backend (takes about 30 seconds to load the model)...
start "UniGuide backend" cmd /k "cd /d %~dp0backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000"

:waitbackend
timeout /t 4 /nobreak >nul
curl -s -o nul -w "%%{http_code}" http://127.0.0.1:8000/api/health | find "200" >nul
if errorlevel 1 goto waitbackend
echo Backend is ready.

echo [3/3] Launching the app on the emulator...
cd /d %~dp0flutter_app
flutter run -d emulator-5554
