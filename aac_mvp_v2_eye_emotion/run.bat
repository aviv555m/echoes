
@echo off
cd /d %~dp0
python -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r backend\requirements.txt
set OLLAMA_MODEL=llama3.2
python backend\app.py
