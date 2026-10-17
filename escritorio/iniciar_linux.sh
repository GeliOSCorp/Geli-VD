#!/bin/bash
# Geli-VD — lanzador para Linux
cd "$(dirname "$0")" || exit 1

if ! command -v python3 >/dev/null 2>&1; then
  echo "No se encontró Python 3.  Debian/Ubuntu:  sudo apt install python3 python3-venv python3-tk"
  exit 1
fi
if ! python3 -c "import tkinter" >/dev/null 2>&1; then
  echo "Falta tkinter.  Debian/Ubuntu:  sudo apt install python3-tk"
  exit 1
fi

if [ ! -x ".venv/bin/python" ]; then
  echo "Primera vez: preparando Geli-VD (puede tardar un par de minutos)…"
  python3 -m venv .venv || { echo "Falta venv.  Debian/Ubuntu:  sudo apt install python3-venv"; exit 1; }
  .venv/bin/python -m pip install --upgrade pip -q
  .venv/bin/python -m pip install -r requirements.txt || exit 1
fi

command -v ffmpeg >/dev/null 2>&1 || echo "Aviso: falta ffmpeg  →  sudo apt install ffmpeg"
command -v deno >/dev/null 2>&1 || [ -x "$HOME/.deno/bin/deno" ] || \
  echo "Aviso: falta deno  →  curl -fsSL https://deno.land/install.sh | sh"

exec .venv/bin/python descargador_video.py
