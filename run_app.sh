#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
if [ -x ".venv/bin/python" ]; then
  PYTHON=".venv/bin/python"
elif [ -x ".venv/Scripts/python.exe" ]; then
  PYTHON=".venv/Scripts/python.exe"
else
  PYTHON="$(command -v python || true)"
fi
if [ -z "$PYTHON" ]; then
  echo 'Python is missing. Install Python 3.11+ and the project requirements first.'
  exit 1
fi
if ! "$PYTHON" -c 'import streamlit' 2>/dev/null; then
  echo 'Streamlit is missing. Install requirements.txt in the project environment first.'
  exit 1
fi
echo 'Open http://localhost:8501 in your browser. Stop with Ctrl+C.'
exec "$PYTHON" -m streamlit run streamlit_app.py
