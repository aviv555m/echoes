import requests, random

class PredictionEngine:
    def __init__(self, model_name='llama3.2', host='http://localhost:11434'):
        self.model = model_name; self.host = host

    def _ollama_generate(self, prompt):
        r = requests.post(f"{self.host}/api/generate", json={
            "model": self.model, "prompt": prompt, "stream": False,
            "options": {"temperature": 0.6, "num_ctx": 2048}
        }, timeout=20)
        r.raise_for_status()
        return ' '.join(r.json().get('response','').split()[:3]).strip()

    def predict_next(self, history, blocked_words=None):
        blocked = set((blocked_words or []))
        try:
            out = self._ollama_generate(
                f"Phrase so far: '{history}'. Suggest a very short AAC-friendly next word/phrase. Keep it simple."
            )
        except Exception:
            out = random.choice(['I want','help','more','stop','yes','no','toilet','drink','eat','play'])
        toks = [t for t in out.split() if t.lower() not in blocked]
        return " ".join(toks) if toks else "..."
