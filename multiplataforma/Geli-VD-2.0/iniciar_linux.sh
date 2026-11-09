#!/bin/bash
cd "$(dirname "$0")" || exit 1
if [ ! -x .venv/bin/python ];then python3 -m venv .venv || exit 1;fi
.venv/bin/python -c 'import PySide6, yt_dlp, PIL, certifi, truststore, playwright.sync_api' 2>/dev/null || .venv/bin/python -m pip install -r requirements.txt || exit 1
.venv/bin/python main.py
