import os
import json
from flask import Flask, render_template, request, jsonify
import requests
from threading import Lock
from datetime import datetime

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
    "pricing_tier": "pro"  # "free" or "pro"
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

@app.route("/")
def index():
    ensure_files()
    data = load_json(PHRASES_PATH)
    settings = load_json(SETTINGS_PATH)
    return render_template("index.html", data=data, settings=settings, app_name=APP_NAME)

@app.post("/api/speak")
def speak():
    """Log a spoken phrase (used for engagement metrics & AI context)."""
    payload = request.get_json(force=True)
    phrase = (payload.get("phrase") or "").strip()
    if not phrase:
        return jsonify({"ok": False, "error": "Empty phrase"}), 400
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
        settings.update({k: v for k, v in payload.items() if k in DEFAULT_SETTINGS})
        save_json(SETTINGS_PATH, settings)
    return jsonify({"ok": True, "settings": settings})

def ollama_chat(messages, model="llama3.2", endpoint="http://localhost:11434/api/chat", temperature=0.2):
    """Call Ollama's chat API with a simple messages list."""
    try:
        resp = requests.post(endpoint, json={"model": model, "messages": messages, "stream": False, "options": {"temperature": temperature}}, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        # Ollama chat returns {"message": {"content": "..."}, ...}
        content = data.get("message", {}).get("content", "")
        return content.strip()
    except Exception as e:
        return ""

@app.post("/api/suggest")
def suggest():
    """Return AI-supported suggestions based on recent history and current text. Falls back if AI unavailable."""
    payload = request.get_json(force=True)
    current_text = (payload.get("current") or "").strip()
    k = int(payload.get("k") or 5)

    data = load_json(PHRASES_PATH)
    history = data.get("history", [])[-10:]
    # Build a simple context
    hist_text = "\n".join([h["phrase"] for h in history])
    system = (
        "You are an AAC assistant helping a user communicate with short, clear everyday phrases. "
        "Given a recent history and a partial input, suggest the next words or short phrases. "
        "Return ONLY a JSON array of up to {k} suggestions, no prose."
    ).format(k=k)
    user = f"History:\n{hist_text}\n\nCurrent input: '{current_text}'\n\nSuggest next phrases."

    # Try Ollama
    suggestions = []
    model_enabled = load_json(SETTINGS_PATH).get("ai_enabled", True)
    if model_enabled:
        raw = ollama_chat([{"role": "system", "content": system}, {"role": "user", "content": user}])
        # Attempt to parse JSON array from response
        try:
            # Find first '[' and last ']'
            start = raw.find('[')
            end = raw.rfind(']') + 1
            if start != -1 and end != -1:
                suggestions = json.loads(raw[start:end])
            else:
                suggestions = []
        except Exception:
            suggestions = []

    # Fallback: frequency-based + prefix match
    if not suggestions:
        counts = {}
        for cat, phrases in data.get("categories", {}).items():
            for p in phrases:
                if (not current_text) or p.lower().startswith(current_text.lower()):
                    counts[p] = counts.get(p, 0) + 1
        # Also include recent history phrases
        for h in history:
            p = h["phrase"]
            if (not current_text) or p.lower().startswith(current_text.lower()):
                counts[p] = counts.get(p, 0) + 2  # prioritize history
        suggestions = sorted(counts.keys(), key=lambda x: (-counts[x], x))[:k]

    return jsonify({"ok": True, "suggestions": suggestions})

# Simple in-memory metrics endpoint (MVP illustrative)
@app.get("/api/metrics")
def metrics():
    data = load_json(PHRASES_PATH)
    history = data.get("history", [])
    now = datetime.utcnow()
    # weekly active = distinct days in last 7
    last7 = [h for h in history if (now - datetime.fromisoformat(h["ts"].replace("Z",""))).days < 7]
    weekly_active_days = len({h["ts"][:10] for h in last7})
    # daily communication events = today's taps
    today = now.date().isoformat()
    todays = len([h for h in history if h["ts"].startswith(today)])
    return jsonify({
        "ok": True,
        "weekly_active_days": weekly_active_days,
        "today_taps": todays,
        "total_phrases": sum(len(v) for v in data.get("categories", {}).values())
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
