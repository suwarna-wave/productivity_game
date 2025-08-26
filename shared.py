# shared.py
import json, os, threading, time

DATA_PATH = os.path.join(os.path.dirname(__file__), "data.json")
_LOCK = threading.Lock()

DEFAULTS = {
    "coins": 0,
    "xp": 0,
    "sessions_completed": 0,
    "options": {
        "focus_minutes": 25,
        "short_break_minutes": 5,
        "long_break_minutes": 15,
        "long_after_n_focus": 2,
        "sound_enabled": True,
    },
    "inventory": {"hat": False, "pet_slime": False},
    "tasks": [],       # list of {id, title, subtasks:[{id,title,weight,done}]}
    "calendar": {},    # "YYYY-MM-DD": {"title": "...", "color": "#RRGGBB", "note": "..."}
    "sessions": []     # list of {start_ts, end_ts, type}  type in {"FOCUS","SHORT","LONG"}
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

def append_session(start_ts, end_ts, kind):
    """Record a completed focus/break session."""
    s = load()
    s.setdefault("sessions", [])
    s["sessions"].append({"start_ts": start_ts, "end_ts": end_ts, "type": kind})
    save(s)

def reward(coins=0, xp=0, sessions_inc=0):
    s = load()
    s["coins"] += coins
    s["xp"] += xp
    s["sessions_completed"] += sessions_inc
    save(s)

def now_ts():
    return int(time.time())
