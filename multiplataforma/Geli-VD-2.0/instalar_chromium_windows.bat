@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" call iniciar_windows.bat
if not exist ".venv\Scripts\python.exe" exit /b 1
echo Instalando Chromium separado para inicio de sesion de Geli-VD...
".venv\Scripts\python.exe" -m pip install "playwright>=1.56,<2"
if errorlevel 1 (pause & exit /b 1)
".venv\Scripts\python.exe" -m playwright install chromium
if errorlevel 1 (pause & exit /b 1)
echo Chromium instalado. Reinicia Geli-VD.
pause
