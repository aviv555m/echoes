from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import cv2
import mediapipe as mp
import threading
import json
import requests
import time

# Initialize Flask
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# MediaPipe
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(min_detection_confidence=0.7, min_tracking_confidence=0.7)

# Webcam Thread
gaze_coords = {"x": 0.5, "y": 0.5}  # normalized

def eye_tracker():
    global gaze_coords
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(frame_rgb)
        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0].landmark
            left_eye = landmarks[33]  # approximate left eye
            right_eye = landmarks[263]  # approximate right eye
            # normalized gaze: midpoint between eyes
            gaze_coords["x"] = (left_eye.x + right_eye.x)/2
            gaze_coords["y"] = (left_eye.y + right_eye.y)/2
            socketio.emit("gaze_update", gaze_coords)
        # Show tracker window
        cv2.imshow("Eye Tracker", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()

threading.Thread(target=eye_tracker, daemon=True).start()

# Load user phrases
try:
    with open("data/user_phrases.json", "r") as f:
        user_phrases = json.load(f)
except:
    user_phrases = {"Needs": ["Water", "Bathroom"], "Feelings": ["Happy", "Sad"], "Daily": ["Eat", "Sleep"]}

# Profanity filter (simple example)
bad_words = ["badword1", "badword2"]

def check_profanity(text):
    for word in bad_words:
        if word.lower() in text.lower():
            return True
    return False

def teach_profanity(text):
    return f"The phrase '{text}' contains a word that is not appropriate. Try using polite words instead."

# AI call placeholder (Ollama llama3.2)
def ai_suggest(text):
    try:
        response = requests.post(
            "http://localhost:11434/completions",
            json={
                "model": "llama3.2",
                "prompt": f"Suggest next phrase for AAC context: '{text}'",
                "max_tokens": 30
            }
        )
        return response.json()["completion"]
    except:
        return "Suggestion unavailable"

@app.route("/")
def index():
    return render_template("index.html", categories=list(user_phrases.keys()), phrases=user_phrases)

@app.route("/select_phrase", methods=["POST"])
def select_phrase():
    data = request.json
    phrase = data.get("phrase")
    if check_profanity(phrase):
        teaching = teach_profanity(phrase)
        return jsonify({"blocked": True, "message": teaching})
    return jsonify({"blocked": False, "message": phrase})

@app.route("/ai_suggest", methods=["POST"])
def ai_suggest_route():
    text = request.json.get("text", "")
    suggestion = ai_suggest(text)
    return jsonify({"suggestion": suggestion})

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
