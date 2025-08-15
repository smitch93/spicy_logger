@echo off
setlocal ENABLEDELAYEDEXPANSION

rem ===== Run Spicy Recipe Logger locally (Windows .bat) =====
rem - Creates venv if missing
rem - Activates venv
rem - Installs/updates deps
rem - Starts the Flask app

rem Jump to this script's directory
cd /d "%~dp0"

rem Pick a Python launcher (prefer `py` on Windows)
where py >nul 2>&1
if %ERRORLEVEL%==0 (
  set "PY=py"
) else (
  set "PY=python"
)

rem Create venv if it doesn't exist
if not exist "venv" (
  echo [setup] Creating virtual environment...
  %PY% -m venv venv
  if not exist "venv" (
    echo [error] Failed to create venv. Is Python installed and on PATH?
    pause
    exit /b 1
  )
)

rem Activate venv
call "venv\Scripts\activate.bat"
if errorlevel 1 (
  echo [error] Could not activate venv. Check venv\Scripts\activate.bat
  pause
  exit /b 1
)

rem Upgrade pip (quiet-ish), then install requirements if present
python -m pip install --upgrade pip
if exist "requirements.txt" (
  echo [deps] Installing from requirements.txt ...
  pip install -r requirements.txt
) else (
  echo [warn] requirements.txt not found. Skipping dependency install.
)

rem Env vars for local dev
set "FLASK_DEBUG=1"

rem Run the app
echo [run] Launching Spicy_Recipe_Logger_App.py ...
python "Spicy_Recipe_Logger_App.py"
set "EXITCODE=%ERRORLEVEL%"

rem Optional: auto-open browser on first run (uncomment next line [tested:rem removed does not auto open browser])
start "" "http://127.0.0.1:5000"

if not "%EXITCODE%"=="0" (
  echo [error] App exited with code %EXITCODE%.
  pause
)

endlocal
