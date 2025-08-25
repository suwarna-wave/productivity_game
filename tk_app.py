# tk_app.py
import tkinter as tk
from tkinter import messagebox
import time, threading, subprocess, sys, os
from shared import load, save

APP_TITLE = "FocusForge — Productivity + Game"
REWARD_PER_SESSION_COINS = 10
REWARD_PER_SESSION_XP = 15

class Pomodoro:
    def __init__(self, root, on_session_complete):
        self.root = root
        self.on_session_complete = on_session_complete
        self.running = False
        self.is_break = False
        self.remaining = 0
        self._timer_thread = None
        self._stop_flag = False

        self.frame = tk.LabelFrame(root, text="Pomodoro", padx=10, pady=10)
        self.frame.pack(fill="x", padx=10, pady=10)

        self.minutes_var = tk.StringVar(value=str(load()["options"]["focus_minutes"]))
        self.break_var   = tk.StringVar(value=str(load()["options"]["break_minutes"]))

        row = tk.Frame(self.frame); row.pack(fill="x")
        tk.Label(row, text="Focus (min):").pack(side="left")
        tk.Entry(row, textvariable=self.minutes_var, width=5).pack(side="left", padx=6)
        tk.Label(row, text="Break (min):").pack(side="left")
        tk.Entry(row, textvariable=self.break_var, width=5).pack(side="left", padx=6)

        self.time_label = tk.Label(self.frame, text="00:00", font=("Arial", 28))
        self.time_label.pack(pady=8)

        button_row = tk.Frame(self.frame); button_row.pack()
        tk.Button(button_row, text="Start Focus", command=self.start_focus).pack(side="left", padx=5)
        tk.Button(button_row, text="Stop", command=self.stop).pack(side="left", padx=5)
        tk.Button(button_row, text="Reset", command=self.reset).pack(side="left", padx=5)
        tk.Button(button_row, text="Save Options", command=self.save_options).pack(side="left", padx=5)

    def save_options(self):
        s = load()
        try:
            focus = max(1, int(self.minutes_var.get()))
            brk   = max(1, int(self.break_var.get()))
        except ValueError:
            messagebox.showerror("Invalid", "Please enter valid integers.")
            return
        s["options"]["focus_minutes"] = focus
        s["options"]["break_minutes"] = brk
        save(s)
        messagebox.showinfo("Saved", "Options updated.")

    def start_focus(self):
        if self.running: return
        minutes = max(1, int(self.minutes_var.get()))
        self.is_break = False
        self.start(minutes*60)

    def start_break(self):
        minutes = max(1, int(self.break_var.get()))
        self.is_break = True
        self.start(minutes*60)

    def start(self, seconds):
        self.running = True
        self._stop_flag = False
        self.remaining = seconds
        self._timer_thread = threading.Thread(target=self._run_timer, daemon=True)
        self._timer_thread.start()

    def stop(self):
        self._stop_flag = True
        self.running = False

    def reset(self):
        self.stop()
        self.remaining = 0
        self.time_label.config(text="00:00")

    def _run_timer(self):
        while self.remaining > 0 and not self._stop_flag:
            mins = self.remaining // 60
            secs = self.remaining % 60
            self.time_label.config(text=f"{mins:02d}:{secs:02d}")
            time.sleep(1)
            self.remaining -= 1

        if self._stop_flag:
            return

        self.running = False
        if self.is_break:
            # Break finished → ready for next focus
            self.time_label.config(text="Break done 🎉")
        else:
            # Focus finished → reward!
            self._reward_and_start_break()

    def _reward_and_start_break(self):
        s = load()
        s["coins"] += REWARD_PER_SESSION_COINS
        s["xp"] += REWARD_PER_SESSION_XP
        s["sessions_completed"] += 1
        save(s)
        self.time_label.config(text="Focus done! +10 coins, +15 XP")
        self.on_session_complete()
        # Auto start break after 3s
        self.root.after(3000, self.start_break)

class TaskList:
    def __init__(self, root):
        self.frame = tk.LabelFrame(root, text="Tasks", padx=10, pady=10)
        self.frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.tasks = []
        self.entry = tk.Entry(self.frame)
        self.entry.pack(fill="x", pady=4)
        tk.Button(self.frame, text="Add Task", command=self.add_task).pack()
        self.list_frame = tk.Frame(self.frame)
        self.list_frame.pack(fill="both", expand=True, pady=6)

    def add_task(self):
        text = self.entry.get().strip()
        if not text: return
        var = tk.BooleanVar(value=False)
        row = tk.Frame(self.list_frame)
        row.pack(fill="x", pady=2)
        cb = tk.Checkbutton(row, text=text, variable=var, onvalue=True, offvalue=False,
                            command=lambda:self._maybe_reward(var))
        cb.pack(side="left")
        self.tasks.append((var, cb))

    def _maybe_reward(self, var):
        if var.get():
            # micro‑reward for checking a task (optional)
            s = load()
            s["coins"] += 2
            s["xp"] += 3
            save(s)

class StatsBar:
    def __init__(self, root):
        self.frame = tk.Frame(root)
        self.frame.pack(fill="x", padx=10, pady=6)
        self.coins_lbl = tk.Label(self.frame, text="Coins: 0")
        self.coins_lbl.pack(side="left", padx=6)
        self.xp_lbl = tk.Label(self.frame, text="XP: 0")
        self.xp_lbl.pack(side="left", padx=6)
        self.sessions_lbl = tk.Label(self.frame, text="Sessions: 0")
        self.sessions_lbl.pack(side="left", padx=6)
        tk.Button(self.frame, text="Open Reward World", command=self.open_game).pack(side="right")
        self.refresh()

    def refresh(self):
        s = load()
        self.coins_lbl.config(text=f"Coins: {s['coins']}")
        self.xp_lbl.config(text=f"XP: {s['xp']}")
        self.sessions_lbl.config(text=f"Sessions: {s['sessions_completed']}")

    def open_game(self):
        # Launch pg_game.py as a subprocess
        here = os.path.dirname(__file__)
        game = os.path.join(here, "pg_game.py")
        py = sys.executable
        try:
            subprocess.Popen([py, game])
        except Exception as e:
            messagebox.showerror("Error", str(e))

def on_session_complete(statsbar):
    statsbar.refresh()

def main():
    root = tk.Tk()
    root.title(APP_TITLE)
    stats = StatsBar(root)
    pom = Pomodoro(root, on_session_complete=lambda: on_session_complete(stats))
    tasks = TaskList(root)

    # Periodically refresh stats (in case Pygame changed them)
    def tick():
        stats.refresh()
        root.after(3000, tick)
    tick()

    root.mainloop()

if __name__ == "__main__":
    main()
