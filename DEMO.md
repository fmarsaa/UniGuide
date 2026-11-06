# UniGuide demo (laptop + phone hotspot)

The backend and the admin portal run on the laptop. The phone joins nothing: the laptop
joins the phone's hotspot, and the phone reaches the laptop over it.

## Shortest steps

1. Phone: turn on the mobile hotspot. Laptop: connect to it.
   (If Windows asks whether to make the network discoverable / private, answer No.)
2. Laptop, in the repo folder:

   ```powershell
   powershell -ExecutionPolicy Bypass -File start_demo.ps1
   ```

   It prints the laptop IP, the server address for the app, the portal address and the
   health check. The health line must say `model_loaded=True model_version=xgb-v4-...`.
3. Phone app: open UniGuide, tap the gear icon at the top right of the sign-in screen,
   type the printed server address (for example `http://192.168.43.10:8000`), tap
   **Test connection** (it must say OK), then **Save**.
4. Phone browser (Chrome): open the printed portal address (for example
   `http://192.168.43.10:5000`) and sign in as the administrator.
5. After the demo: `powershell -ExecutionPolicy Bypass -File stop_demo.ps1`

## Installing the APK

File: `flutter_app/build/app/outputs/flutter-apk/app-release.apk` (version 1.0.0-demo).

- USB: copy the file to the phone's Downloads folder and open it there, or
  `adb install -r flutter_app\build\app\outputs\flutter-apk\app-release.apk`
- Google Drive: upload the file, open it on the phone, tap Install.

Android asks once to allow installing from that source (Files / Drive / Chrome); allow it.
The APK is signed with the Android debug certificate, so Play Protect may warn that the
app is from an unknown developer; choose to install anyway.

## Accounts

- Administrator: fatmamarsa2@gmail.com
- Student: fatumamm99@gmail.com

Both are email-verified. Passwords are not stored in this repository. In the portal,
sign in with email and password (Google sign-in was not tested from a plain IP address).

## Three demo profiles

Expected results are in `logs/demo_profiles.txt` (v4 model).

1. Strong science student: mean A-; Maths A, English B+, Kiswahili B, Chemistry A,
   Biology A, Physics A-, Geography B+; interests Healthcare & Clinical Medicine and
   Clinical Laboratory & Diagnostic Sciences; strengths Logical & Analytical Reasoning
   and Empathy & Human Care; career Medical Doctor (Physician/Surgeon).
2. Undecided student: mean B; Maths B, English B+, Kiswahili B, Chemistry B-,
   Biology B, History & Government A-, Business Studies B+; interests Journalism & Media
   Production and Social Research & Community Development; strengths Team Collaboration
   and Creative Problem Solving; career Not sure yet.
3. C+ mean, meets no programme's subject requirements: mean C+; Maths D+, English C-,
   Kiswahili B, Chemistry D+, CRE A, Home Science B+, Art & Design B-; interest
   Hospitality & Guest Services; strength Creative Problem Solving; career Not sure yet.
   Expected: no programmes and the message "No programmes match your subject grades."

## If something does not work

- App says it cannot reach the server: check the laptop is still on the hotspot, run
  `ipconfig` (look for the Wi-Fi "IPv4 Address"), and re-enter that address in the gear
  dialog. Then check `http://<ip>:8000/api/health` in the phone's browser.
- Health check gives no answer: see `logs\demo_backend_err.log`, then run
  `stop_demo.ps1` and `start_demo.ps1` again.
- Portal shows errors after sign-in: start_demo.ps1 allows the portal address it printed;
  if the IP changed, run start_demo.ps1 again.

## Pre-demo checklist

- [ ] Laptop charged; Chrome and other heavy programs closed.
- [ ] Phone hotspot on, laptop connected.
- [ ] `start_demo.ps1` health line shows model_loaded=True and xgb-v4.
- [ ] App: gear, server address, Test connection says OK, Save.
- [ ] Student sign-in works and a profile gives recommendations.
- [ ] Portal opens on the phone and the administrator can sign in.
- [ ] One cutoff edit in the portal saves and appears in the audit log.

## Checks already run

- `logs/demo_smoke.txt`, `logs/demo_portal_lan_check.txt`: health, programmes, CORS for
  the portal origin, sign-in required, and the app flows (role, recommendations, saved
  history, what-if, career note, compare data, shortlist, feedback, admin cutoff update,
  audit log, analytics) through the backend code with an in-memory database.
- `logs/demo_apk_build.txt`, `logs/demo_apk_info.txt`, `logs/demo_web_build.txt`.
