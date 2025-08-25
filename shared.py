# shared.py
import json, os, threading

DATA_PATH = os.path.join(os.path.dirname(__file__), "data.json")
_LOCK = threading.Lock()

DEFAULTS = {
    "coins": 0,
    "xp": 0,
    "sessions_completed": 0,
    "options": {"focus_minutes": 25, "break_minutes": 5},
    "inventory": {"hat": False, "pet_slime": False}
}

def _ensure():
    if not os.path.exists(DATA_PATH):
        save(DEFAULTS)

def load():
    _ensure()
    with _LOCK:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

def save(state):
    with _LOCK:
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
