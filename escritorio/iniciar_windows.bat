@echo off
rem Geli-VD - lanzador para Windows (doble clic)
chcp 65001 >nul
cd /d "%~dp0"

set "PY="
where py >nul 2>&1 && set "PY=py -3"
if not defined PY where python >nul 2>&1 && set "PY=python"
if not defined PY (
  echo No se encontro Python. Instalalo desde https://www.python.org/downloads/
  echo y marca la casilla "Add python.exe to PATH".
  pause & exit /b 1
)

if not exist ".venv\Scripts\pythonw.exe" (
  echo Primera vez: preparando Geli-VD ^(puede tardar un par de minutos^)...
  %PY% -m venv .venv || (echo No se pudo crear el entorno. & pause & exit /b 1)
  ".venv\Scripts\python.exe" -m pip install --upgrade pip -q
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt || (echo Fallo la instalacion. & pause & exit /b 1)
)

where ffmpeg >nul 2>&1 || echo Aviso: falta ffmpeg  -^>  winget install Gyan.FFmpeg
where deno   >nul 2>&1 || echo Aviso: falta deno    -^>  winget install DenoLand.Deno

start "" ".venv\Scripts\pythonw.exe" descargador_video.py
