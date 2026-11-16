@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  python -m venv .venv
  if errorlevel 1 (
    echo Failed to create .venv. Is Python on PATH?
    exit /b 1
  )
)

".venv\Scripts\python.exe" -c "import fastapi, uvicorn, pandas, sklearn" 1>nul 2>nul
if errorlevel 1 (
  echo Installing dependencies into .venv...
  ".venv\Scripts\python.exe" -m pip install --upgrade pip
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 (
    echo Failed to install requirements.
    exit /b 1
  )
)

echo Starting server at http://127.0.0.1:8765
".venv\Scripts\python.exe" server.py
endlocal
