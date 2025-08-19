# Echoes MVP v2 (Python + Flask + Ollama + Eye Tracking)

Adds **webcam eye/face tracking** and an **AI profanity-teaching filter** to the Echoes AAC MVP.

## Features
- **Grid AAC board** with tap-to-speak (browser SpeechSynthesis).
- **AI suggestions** using **Ollama llama3.2**.
- **Custom phrases & categories**.
- **Eye & Face Tracker** (OpenCV + MediaPipe) opens a native window showing landmarks; press **Q** to close.
- **Profanity Filter + Teaching**: if a phrase is inappropriate, the app blocks speech and shows a short, supportive teaching message from the AI.
- **Offline-first**: core works offline; AI requires local Ollama only.
- **Basic metrics**: `/api/metrics` includes eye tracker running status.

## Prerequisites
- Python 3.10+
- **Ollama** installed & running (`http://localhost:11434`)
  ```bash
  ollama pull llama3.2
  ```

## Setup
```bash
cd echoes_mvp_v2
python -m venv .venv
# Windows PowerShell
. .venv\Scripts\Activate.ps1
# Linux/macOS
# source .venv/bin/activate

pip install -r requirements.txt
python app.py
```
Open: http://localhost:5000

## Eye Tracker
- Autostarts when the site loads (if enabled in settings).
- Toggle in the header. A native OpenCV window titled **"Echoes Eye & Face Tracker"** will appear.
- Press **Q** in that window to stop it.

## Profanity Teaching
- Local fast check catches common offensive words.
- If detected, the backend asks **llama3.2** to generate a kind, brief explanation + alternatives.
- The UI shows this message and prevents speaking that phrase.

## Notes
- This MVP stores data in `data/*.json`. Add multi-user auth/storage later.
- To integrate gaze selection in the UI, we can send simple events from the tracker to the web UI or run the tracker in WebAssembly (e.g., MediaPipe Tasks JS). This build keeps the tracker native for performance and simplicity.
