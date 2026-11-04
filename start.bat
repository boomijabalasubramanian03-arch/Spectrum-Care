@echo off
setlocal EnableExtensions
cd /d "%~dp0"

 title Chroma Context Setup and Launcher
 echo =====================================================
 echo   Chroma Context - Local / Offline-capable launcher
 echo =====================================================
 echo.

if exist backend\venv\Scripts\python.exe (
  echo [1/4] Using existing virtual environment.
  goto env_ready
)

REM Check for Python 3.12 via py launcher or local install
set "PYTHON_EXE="
py -3.12 --version >nul 2>nul && set "PYTHON_EXE=py -3.12"
if not defined PYTHON_EXE if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"

if not defined PYTHON_EXE (
  echo Python 3.12 was not found.
  echo Please install Python 3.12.x from https://www.python.org/downloads/release/python-31210/
  pause
  exit /b 1
)

if not exist backend\venv\Scripts\python.exe (
  echo [1/4] Creating a Python 3.12 virtual environment...
  %PYTHON_EXE% -m venv backend\venv
  if errorlevel 1 (echo Could not create the virtual environment.& pause & exit /b 1)
)

:env_ready

if not exist backend\venv\.deps_installed (
  echo [2/4] Installing Python packages. Internet is needed for first-time setup.
  call backend\venv\Scripts\python.exe -m pip install --upgrade pip
  if errorlevel 1 (echo pip upgrade failed. Check internet and try again.& pause & exit /b 1)
  call backend\venv\Scripts\python.exe -m pip install -r backend\requirements.txt
  if errorlevel 1 (echo Python dependencies failed to install. See the error above.& pause & exit /b 1)
  echo installed> backend\venv\.deps_installed
) else (
  echo [2/4] Python dependencies already installed.
)

if not exist frontend\dist\index.html (
  where npm >nul 2>nul
  if errorlevel 1 (
    echo Node.js / npm was not found. Install Node.js 20 LTS or newer, then retry.
    pause
    exit /b 1
  )
  echo [3/4] Installing frontend dependencies and building the UI.
  echo This step needs internet on the first run only.
  pushd frontend
  call npm ci
  if errorlevel 1 (popd & echo npm ci failed. Check internet and package-lock.json.& pause & exit /b 1)
  call npm run build
  if errorlevel 1 (popd & echo Frontend build failed. See the error above.& pause & exit /b 1)
  popd
) else (
  echo [3/4] Frontend build already exists.
)

echo [4/4] Creating/verifying the local SQLite database tables...
call backend\venv\Scripts\python.exe backend\init_db.py
if errorlevel 1 (echo Database initialization failed. See the error above.& pause & exit /b 1)

echo.
echo Starting Chroma Context at http://localhost:8000
 echo First-time setup is complete; subsequent local runs do not need internet.
 echo Close this window or press Ctrl+C to stop the backend.
 echo.
start "" http://localhost:8000
cd backend
call venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
pause
