# Smart Adaptive AAC — v2 (Eye Tracking + Fixed Emotion, Ollama llama3.2)

This version moves **emotion detection** and **eye tracking** fully to the **browser** (no OpenCV needed),
so it works reliably on Windows without extra native files.

## What changed vs v1
- ✅ **Emotion detection**: uses MediaPipe **Face Landmarker** blendshapes in the browser.
  - Maps blendshape scores to simple emotions: happiness, sadness, anger, tired, neutral.
  - UI adapts text rate/layout hint accordingly.
- ✅ **Eye tracking**: uses **WebGazer.js** (browser-based gaze estimation) with **dwell selection**.
  - Highlights the grid cell where the user looks; selects after ~1.2s dwell.
- ✅ Backend simplified (no OpenCV/mediapipe/onnx). API is the same for predictions/controls/referrals.
- ✅ Still uses **Ollama `llama3.2`** for predictions at `http://127.0.0.1:11434`.

## Prereqs
- Python 3.10+
- Ollama with `llama3.2`:
  ```bash
  ollama pull llama3.2
  ollama serve
  ```

## Run backend
Windows:
```bat
run.bat
```
macOS/Linux:
```bash
bash run.sh
```

Backend at: **http://127.0.0.1:8000**

## Open frontend
Either open `frontend/index.html` directly, or serve it (recommended for camera permissions):
```bash
python -m http.server 8080 --directory frontend
```
Visit: **http://localhost:8080**

## How emotion works
- We load MediaPipe **Face Landmarker** (WASM + model) from CDN.
- Every frame, we run blendshape inference and convert to labels:
  - `mouthSmile` → happiness
  - `browDown + mouthFrown` → anger
  - `mouthFrown` (no smile) → sadness
  - `eyeBlink` high → tired
  - else → neutral

## How eye tracking works
- We load **WebGazer.js** (no calibration required for MVP).
- Gaze X/Y projected over the AAC grid; the hovered cell is highlighted.
- **Dwell**: if the gaze stays on the same cell for ~1.2s, it auto-selects (click).

> You can later enable WebGazer calibration (`webgazer.showPredictionPoints(true)`) for better accuracy.

## Parent dashboard & referrals
- Same as v1: block words, claim referrals, see plan upgrades.
- Plans: Basic → Basic Plus (3) → Basic Pro (5) → Basic Max (8) → Elite (12).

## Notes
- All emotion/eye processing happens **locally** in the browser; no video leaves the device.
- If **Ollama** is not running, suggestions fall back to a small AAC list.
- Input optimizer still aggregates speed/accuracy and reports the best method.

