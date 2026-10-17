#!/bin/bash
# Geli-VD — lanzador para macOS (doble clic)
cd "$(dirname "$0")" || exit 1
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

if ! command -v python3 >/dev/null 2>&1; then
  echo "No se encontró Python 3. Instálalo desde https://www.python.org/downloads/ y vuelve a intentar."
  read -r -p "Presiona Enter para cerrar…"; exit 1
fi
if ! python3 -c "import tkinter" >/dev/null 2>&1; then
  echo "Tu Python no tiene tkinter (la parte gráfica)."
  echo "Si usas Python de Homebrew, ejecuta:  brew install python-tk"
  echo "o instala Python desde https://www.python.org/downloads/"
  read -r -p "Presiona Enter para cerrar…"; exit 1
fi

if [ ! -x ".venv/bin/python" ]; then
  echo "Primera vez: preparando Geli-VD (puede tardar un par de minutos)…"
  python3 -m venv .venv || { read -r -p "No se pudo crear el entorno. Enter para cerrar…"; exit 1; }
  .venv/bin/python -m pip install --upgrade pip -q
  .venv/bin/python -m pip install -r requirements.txt || { read -r -p "Falló la instalación. Enter para cerrar…"; exit 1; }
fi

command -v ffmpeg >/dev/null 2>&1 || echo "Aviso: falta ffmpeg  →  brew install ffmpeg"
command -v deno   >/dev/null 2>&1 || echo "Aviso: falta deno    →  brew install deno"

nohup .venv/bin/python descargador_video.py >/dev/null 2>&1 &
echo "Geli-VD abierto. Ya puedes cerrar esta ventana."
exit 0
