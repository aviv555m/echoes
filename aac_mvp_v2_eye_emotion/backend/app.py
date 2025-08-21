import os, time
from flask import Flask, request, jsonify
from flask_cors import CORS
from modules.input_optimizer import InputOptimizer
from modules.prediction_engine import PredictionEngine
from modules.referral_system import ReferralSystem
from modules.parent_controls import ParentControls
from modules.db import init_db

app = Flask(__name__)
CORS(app)

init_db()
optimizer = InputOptimizer()
predictor = PredictionEngine(model_name=os.environ.get("OLLAMA_MODEL","llama3.2"))
referrals = ReferralSystem()
controls = ParentControls()

@app.get('/api/health')
def health():
    return jsonify({"status":"ok","time": time.time()})

@app.post('/api/predict')
def predict():
    data = request.get_json(force=True)
    history = data.get('history','')
    suggestion = predictor.predict_next(history, blocked_words=controls.get_blocklist())
    return jsonify({"suggestion": suggestion})

@app.post('/api/input/metrics')
def input_metrics():
    data = request.get_json(force=True)
    method = optimizer.update_and_choose(data)
    return jsonify({"best_method": method})

# Parent controls
@app.get('/api/parent/blocklist')
def get_blocklist():
    return jsonify({"blocked": controls.get_blocklist()})

@app.post('/api/parent/blocklist')
def add_block():
    word = request.get_json(force=True).get('word','').strip().lower()
    if not word:
        return jsonify({"ok":False,"error":"missing word"}), 400
    controls.block_word(word)
    return jsonify({"ok":True})

@app.delete('/api/parent/blocklist')
def del_block():
    word = request.get_json(force=True).get('word','').strip().lower()
    controls.unblock_word(word)
    return jsonify({"ok":True})

@app.post('/api/parent/lock_settings')
def lock():
    locked = bool(request.get_json(force=True).get('locked', True))
    controls.lock_settings(locked)
    return jsonify({"locked": controls.is_locked()})

@app.get('/api/parent/lock_settings')
def get_lock():
    return jsonify({"locked": controls.is_locked()})

# Referrals
@app.post('/api/referrals/claim')
def claim():
    data = request.get_json(force=True)
    ok = referrals.record_referral(data.get('referrer_email'), data.get('joined_email'))
    return jsonify({"ok": ok})

@app.get('/api/referrals/plan')
def plan():
    email = request.args.get('email','')
    return jsonify({"email": email, "plan": referrals.get_plan_for(email)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)), debug=True)
