@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (set "PY=py -3") else (set "PY=python")
if not exist ".venv\Scripts\python.exe" %PY% -m venv .venv
if not exist ".venv\Scripts\python.exe" (echo No se pudo crear el entorno Python.& pause & exit /b 1)
".venv\Scripts\python.exe" -c "import PySide6, yt_dlp, PIL, certifi, truststore, playwright.sync_api"
if errorlevel 1 (
    echo Preparando dependencias del primer inicio...
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 (echo Error instalando dependencias.&pause&exit /b 1)
)
".venv\Scripts\python.exe" main.py
if errorlevel 1 pause
