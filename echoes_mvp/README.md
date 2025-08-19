# Echoes MVP (Python + Flask + Ollama llama3.2)

A lightweight AAC (Augmentative & Alternative Communication) MVP. 
- Grid-based communication board with tap-to-speak (browser TTS).
- AI-assisted next-phrase suggestions via **Ollama** using **llama3.2** (local, offline-friendly).
- Add custom phrases & categories.
- Offline-first UI; AI works without internet when Ollama is running locally.
- Basic metrics endpoints for MVP success tracking.

## Prerequisites

- Python 3.10+
- **Ollama** installed and running locally.
  - Install: https://ollama.com
  - Pull model: `ollama pull llama3.2`
  - Run the server (usually auto): it listens on `http://localhost:11434`

## Setup

```bash
cd echoes_mvp
python -m venv .venv
# On Windows PowerShell:
. .venv\Scripts\Activate.ps1
# On Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt
python app.py
```

Now open http://localhost:5000

## Using AI Suggestions

- The app calls Ollama Chat API at `http://localhost:11434/api/chat` with model `llama3.2`.
- If the model is not running or errors occur, the app falls back to simple frequency/prefix suggestions.

## Pricing Tiers (MVP behavior)

- Free: core board + speech + limited phrases
- Pro (toggle via settings JSON): unlocks richer AI suggestions (this is illustrative; wire up billing later).

## Files

- `app.py` – Flask backend and simple JSON storage.
- `templates/index.html` – UI with board, composer, suggestions.
- `static/js/app.js` – Frontend logic, browser TTS, AI calls.
- `static/css/styles.css` – Minimal modern styling.
- `data/user_phrases.json` – Saved phrases & history.
- `data/settings.json` – Voice/language/theme/flags.

## Notes

- Speech output uses **browser** `speechSynthesis` (works on Chrome/Edge mobile/desktop). 
- To package as a mobile app later, wrap this PWA with Capacitor or Tauri Mobile, or rebuild in Flutter/React Native.
- Security: This MVP stores data locally on the server’s filesystem for simplicity. Add auth & per-user storage for production.
