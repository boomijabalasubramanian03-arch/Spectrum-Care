@echo off
setlocal
cd /d "%~dp0"

echo ================================================
echo   Chroma Context - OFFLINE START
 echo ================================================
 echo.

if not exist backend\venv\Scripts\python.exe (
  echo Python environment not found. Run start.bat once while online first.
  pause
  exit /b 1
)
if not exist frontend\dist\index.html (
  echo Built frontend not found. Run start.bat once while online first.
  pause
  exit /b 1
)

echo Verifying local database tables...
call backend\venv\Scripts\python.exe backend\init_db.py
if errorlevel 1 (pause & exit /b 1)

echo Starting local app at http://localhost:8000 (no internet required).
start "" http://localhost:8000
cd backend
call venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
pause
