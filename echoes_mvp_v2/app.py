import os
import re
import json
import threading
from threading import Lock
from datetime import datetime

from flask import Flask, render_template, request, jsonify
import requests

# Optional (installed via requirements.txt)
import cv2
import mediapipe as mp

APP_NAME = "Echoes MVP"
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
PHRASES_PATH = os.path.join(DATA_DIR, "user_phrases.json")
SETTINGS_PATH = os.path.join(DATA_DIR, "settings.json")

lock = Lock()

DEFAULT_CATEGORIES = {
    "Needs": ["I need help", "I'm thirsty", "I'm hungry", "I need the bathroom", "Please wait"],
    "Feelings": ["I'm happy", "I'm sad", "I'm excited", "I'm tired", "I'm frustrated"],
    "Daily": ["Good morning", "Thank you", "Yes", "No", "Please", "Can we go?"],
    "People": ["Mom", "Dad", "Teacher", "Friend", "Nurse"]
}

DEFAULT_SETTINGS = {
    "voice": "default",
    "language": "en-US",
    "theme": "light",
    "ai_enabled": True,
    "offline_first": True,
    "pricing_tier": "free",  # "free" or "pro"
    "eye_tracker_enabled": True
}

def ensure_files():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(PHRASES_PATH):
        with open(PHRASES_PATH, "w", encoding="utf-8") as f:
            json.dump({"categories": DEFAULT_CATEGORIES, "history": []}, f, ensure_ascii=False, indent=2)
    if not os.path.exists(SETTINGS_PATH):
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_SETTINGS, f, ensure_ascii=False, indent=2)

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

ensure_files()

app = Flask(__name__)

# ---------- Ollama integration ----------
def ollama_chat(messages, model="llama3.2", endpoint="http://localhost:11434/api/chat", temperature=0.2):
    """Call Ollama's chat API with messages. Returns string content or '' on failure."""
    try:
        resp = requests.post(
            endpoint,
            json={
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {"temperature": temperature},
            },
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data.get("message", {}).get("content", "")
        return (content or "").strip()
    except Exception:
        return ""

# ---------- Profanity detection & teaching ----------
_PROFANE_WORDS = [
    "damn","shit","fuck","bitch","bastard","asshole","dick","crap","stupid","idiot",
    "moron","retard","slut","whore","racist","kill yourself","kys"
]
import re
_PROFANE_RE = re.compile(r"(" + "|".join(re.escape(w) for w in _PROFANE_WORDS) + r")", re.IGNORECASE)

BAD_WORD_SYSTEM_PROMPT = """You are a supportive AAC assistant for kids and adults.
If the provided phrase includes profanity, slurs, or insulting language, respond in a short, kind way:
- Say that the word(s) are not okay to use.
- Explain briefly why they can hurt people.
- Offer 2-3 friendly alternatives the user can say instead.
Keep it under 80 words. Keep the tone gentle and encouraging.
If the phrase is fine, respond with: OK
"""

def detect_profanity(text: str) -> bool:
    return bool(_PROFANE_RE.search(text or ""))

def teach_about_profanity(phrase: str) -> str:
    msg = [
        {"role": "system", "content": BAD_WORD_SYSTEM_PROMPT},
        {"role": "user", "content": f"Phrase: {phrase}\nEvaluate and respond."}
    ]
    out = ollama_chat(msg) or ""
    return out

# ---------- Eye / Face tracking (OpenCV + MediaPipe) ----------
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils

_eye_thread = None
_eye_thread_running = False

def eye_tracker_loop():
    global _eye_thread_running
    _eye_thread_running = True
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[EyeTracker] Could not open webcam.")
        _eye_thread_running = False
        return

    with mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as face_mesh:
        while _eye_thread_running and cap.isOpened():
            ok, frame = cap.read()
            if not ok:
                break
            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = face_mesh.process(rgb)

            if result.multi_face_landmarks:
                for fl in result.multi_face_landmarks:
                    mp_drawing.draw_landmarks(
                        image=frame,
                        landmark_list=fl,
                        connections=mp_face_mesh.FACEMESH_TESSELATION,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=mp_drawing.DrawingSpec(thickness=1, circle_radius=1)
                    )
            cv2.imshow("Echoes Eye & Face Tracker (press Q to close)", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()
    _eye_thread_running = False

def start_eye_tracker():
    global _eye_thread
    if _eye_thread and _eye_thread.is_alive():
        return
    _eye_thread = threading.Thread(target=eye_tracker_loop, daemon=True)
    _eye_thread.start()

def stop_eye_tracker():
    global _eye_thread_running
    _eye_thread_running = False

# ---------- Routes ----------
@app.route("/")
def index():
    ensure_files()
    data = load_json(PHRASES_PATH)
    settings = load_json(SETTINGS_PATH)
    if settings.get("eye_tracker_enabled", True):
        start_eye_tracker()
    return render_template("index.html", data=data, settings=settings, app_name=APP_NAME)

@app.post("/api/speak")
def speak():
    payload = request.get_json(force=True)
    phrase = (payload.get("phrase") or "").strip()
    if not phrase:
        return jsonify({"ok": False, "error": "Empty phrase"}), 400

    profane = detect_profanity(phrase)
    ai_warning = ""
    if profane:
        ai_warning = teach_about_profanity(phrase)

    if ai_warning and ai_warning.strip().lower() != "ok":
        return jsonify({"ok": False, "warning": ai_warning})

    with lock:
        data = load_json(PHRASES_PATH)
        data.setdefault("history", []).append({
            "ts": datetime.utcnow().isoformat() + "Z",
            "phrase": phrase
        })
        save_json(PHRASES_PATH, data)
    return jsonify({"ok": True})

@app.get("/api/custom_phrase")
def list_custom():
    data = load_json(PHRASES_PATH)
    return jsonify({"ok": True, "categories": data.get("categories", {})})

@app.post("/api/custom_phrase")
def add_custom():
    payload = request.get_json(force=True)
    category = (payload.get("category") or "Custom").strip() or "Custom"
    phrase = (payload.get("phrase") or "").strip()
    if not phrase:
        return jsonify({"ok": False, "error": "Empty phrase"}), 400
    with lock:
        data = load_json(PHRASES_PATH)
        cats = data.setdefault("categories", {})
        cats.setdefault(category, [])
        if phrase not in cats[category]:
            cats[category].append(phrase)
        save_json(PHRASES_PATH, data)
    return jsonify({"ok": True, "categories": data["categories"]})

@app.delete("/api/custom_phrase")
def delete_custom():
    payload = request.get_json(force=True)
    category = (payload.get("category") or "").strip()
    phrase = (payload.get("phrase") or "").strip()
    with lock:
        data = load_json(PHRASES_PATH)
        cats = data.get("categories", {})
        if category in cats and phrase in cats[category]:
            cats[category].remove(phrase)
            save_json(PHRASES_PATH, data)
            return jsonify({"ok": True, "categories": data["categories"]})
    return jsonify({"ok": False, "error": "Not found"}), 404

@app.get("/api/settings")
def get_settings():
    return jsonify(load_json(SETTINGS_PATH))

@app.post("/api/settings")
def set_settings():
    payload = request.get_json(force=True)
    with lock:
        settings = load_json(SETTINGS_PATH)
        for k in list(payload.keys()):
            if k not in DEFAULT_SETTINGS:
                payload.pop(k, None)
        settings.update(payload)
        save_json(SETTINGS_PATH, settings)
    if settings.get("eye_tracker_enabled", True):
        start_eye_tracker()
    else:
        stop_eye_tracker()
    return jsonify({"ok": True, "settings": settings})

@app.post("/api/suggest")
def suggest():
    payload = request.get_json(force=True)
    current_text = (payload.get("current") or "").strip()
    k = int(payload.get("k") or 5)

    data = load_json(PHRASES_PATH)
    history = data.get("history", [])[-10:]
    hist_text = "\\n".join([h["phrase"] for h in history])

    system = (
        "You are an AAC assistant helping a user communicate with short, clear everyday phrases. "
        f"Given a recent history and a partial input, suggest the next words or short phrases. "
        f"Return ONLY a JSON array of up to {k} suggestions, no prose."
    )
    user = f"History:\\n{hist_text}\\n\\nCurrent input: '{current_text}'\\n\\nSuggest next phrases."

    suggestions = []
    model_enabled = load_json(SETTINGS_PATH).get("ai_enabled", True)
    if model_enabled:
        raw = ollama_chat([{"role": "system", "content": system}, {"role": "user", "content": user}])
        try:
            start = raw.find('[')
            end = raw.rfind(']') + 1
            if start != -1 and end != -1:
                suggestions = json.loads(raw[start:end])
        except Exception:
            suggestions = []

    if not suggestions:
        counts = {}
        for cat, phrases in data.get("categories", {}).items():
            for p in phrases:
                if (not current_text) or p.lower().startswith(current_text.lower()):
                    counts[p] = counts.get(p, 0) + 1
        for h in history:
            p = h["phrase"]
            if (not current_text) or p.lower().startswith(current_text.lower()):
                counts[p] = counts.get(p, 0) + 2
        suggestions = sorted(counts.keys(), key=lambda x: (-counts[x], x))[:k]

    return jsonify({"ok": True, "suggestions": suggestions})

@app.get("/api/metrics")
def metrics():
    data = load_json(PHRASES_PATH)
    history = data.get("history", [])
    now = datetime.utcnow()
    last7 = [h for h in history if (now - datetime.fromisoformat(h["ts"].replace("Z",""))).days < 7]
    weekly_active_days = len({h["ts"][:10] for h in last7})
    today = now.date().isoformat()
    todays = len([h for h in history if h["ts"].startswith(today)])
    return jsonify({
        "ok": True,
        "weekly_active_days": weekly_active_days,
        "today_taps": todays,
        "total_phrases": sum(len(v) for v in data.get("categories", {}).values()),
        "eye_tracker_running": _eye_thread_running
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    if load_json(SETTINGS_PATH).get("eye_tracker_enabled", True):
        start_eye_tracker()
    app.run(host="0.0.0.0", port=port, debug=True)
