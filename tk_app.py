# tk_app.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, colorchooser
import time, threading, calendar, datetime as dt, random
try:
    import winsound
    HAS_WINSOUND = True
except Exception:
    HAS_WINSOUND = False

from shared import load, save, reward, append_session, now_ts
import subprocess, sys, os

APP_TITLE = "FocusForge — Productivity + Game"
REWARD_FOCUS_COINS = 10
REWARD_FOCUS_XP    = 15
REWARD_SUBTASK_COINS_PER_PCT = 0.1   # e.g., weight 20% -> 2 coins
REWARD_SUBTASK_XP_PER_PCT    = 0.15  # e.g., weight 20% -> 3 xp

# ---------- utilities

def play_beep(kind="ok", root=None):
    """Small cross-platform alert. Respects settings.sound_enabled."""
    s = load()
    if not s["options"].get("sound_enabled", True):
        return
    if HAS_WINSOUND:
        if kind == "start":  winsound.Beep(880, 120)
        elif kind == "end":  winsound.Beep(1046, 180)
        else:                winsound.Beep(740, 120)
    else:
        # fallback: tk bell
        try:
            (root or tk._default_root).bell()
        except Exception:
            pass

def nice_time(seconds):
    m, s = divmod(max(0, int(seconds)), 60)
    return f"{m:02d}:{s:02d}"

# ---------- Pomodoro tab

class PomodoroTab(ttk.Frame):
    def __init__(self, master, stats_refresh_cb):
        super().__init__(master)
        self.stats_refresh_cb = stats_refresh_cb
        self.running = False
        self.current_kind = "FOCUS"  # or SHORT or LONG
        self.completed_focus_in_cycle = 0
        self.start_ts = None
        self.remaining = 0
        self.stop_flag = False
        self.timer_thread = None

        # controls
        self.title = ttk.Label(self, text="Pomodoro", font=("Segoe UI", 16, "bold"))
        self.title.pack(pady=(6,2))

        # timer display
        self.time_lbl = ttk.Label(self, text="00:00", font=("Consolas", 36))
        self.time_lbl.pack(pady=4)

        # buttons
        row = ttk.Frame(self); row.pack()
        ttk.Button(row, text="Start Focus", command=self.start_focus).pack(side="left", padx=5)
        ttk.Button(row, text="Stop", command=self.stop).pack(side="left", padx=5)
        ttk.Button(row, text="Reset", command=self.reset).pack(side="left", padx=5)

        # options
        self.opts = load()["options"]
        optf = ttk.LabelFrame(self, text="Options"); optf.pack(padx=8, pady=8, fill="x")
        self.var_focus = tk.IntVar(value=self.opts.get("focus_minutes",25))
        self.var_short = tk.IntVar(value=self.opts.get("short_break_minutes",5))
        self.var_long  = tk.IntVar(value=self.opts.get("long_break_minutes",15))
        self.var_after = tk.IntVar(value=self.opts.get("long_after_n_focus",2))
        self.var_sound = tk.BooleanVar(value=self.opts.get("sound_enabled", True))

        for text,var in [("Focus (min)",self.var_focus),("Short break (min)",self.var_short),
                         ("Long break (min)",self.var_long),("Long break after N focus",self.var_after)]:
            r = ttk.Frame(optf); r.pack(fill="x", pady=2)
            ttk.Label(r, text=text, width=22).pack(side="left")
            ttk.Entry(r, textvariable=var, width=6).pack(side="left")

        r = ttk.Frame(optf); r.pack(fill="x", pady=2)
        ttk.Checkbutton(r, text="Sound alerts", variable=self.var_sound).pack(side="left")
        ttk.Button(optf, text="Save Options", command=self.save_options).pack(pady=6)

        self.status = ttk.Label(self, text="Ready.")
        self.status.pack(pady=(0,6))

    # ---- state & logic
    def save_options(self):
        s = load()
        s["options"]["focus_minutes"] = max(1, self.var_focus.get())
        s["options"]["short_break_minutes"] = max(1, self.var_short.get())
        s["options"]["long_break_minutes"] = max(1, self.var_long.get())
        s["options"]["long_after_n_focus"] = max(1, self.var_after.get())
        s["options"]["sound_enabled"] = bool(self.var_sound.get())
        save(s)
        self.opts = s["options"]
        messagebox.showinfo("Saved", "Timer options updated.")

    def start_focus(self):
        if self.running: return
        self.current_kind = "FOCUS"
        self._start(self.opts.get("focus_minutes",25)*60)
        self.status.config(text="Focus started.")
        play_beep("start", self)

    def start_short(self):
        self.current_kind = "SHORT"
        self._start(self.opts.get("short_break_minutes",5)*60)
        self.status.config(text="Short break.")
        play_beep("start", self)

    def start_long(self):
        self.current_kind = "LONG"
        self._start(self.opts.get("long_break_minutes",15)*60)
        self.status.config(text="Long break.")
        play_beep("start", self)

    def _start(self, seconds):
        self.running = True
        self.stop_flag = False
        self.start_ts = now_ts()
        self.remaining = seconds
        self.timer_thread = threading.Thread(target=self._run_timer, daemon=True)
        self.timer_thread.start()

    def stop(self):
        self.stop_flag = True
        self.running = False
        self.status.config(text="Stopped.")

    def reset(self):
        self.stop()
        self.remaining = 0
        self.time_lbl.config(text="00:00")

    def _run_timer(self):
        while self.remaining > 0 and not self.stop_flag:
            self.time_lbl.config(text=nice_time(self.remaining))
            time.sleep(1)
            self.remaining -= 1

        if self.stop_flag:
            return
        # finished
        self.running = False
        end_ts = now_ts()
        append_session(self.start_ts, end_ts, self.current_kind)

        if self.current_kind == "FOCUS":
            # reward
            reward(REWARD_FOCUS_COINS, REWARD_FOCUS_XP, 1)
            self.completed_focus_in_cycle += 1
            play_beep("end", self)
            self.stats_refresh_cb()
            self.status.config(text=f"Focus finished! +{REWARD_FOCUS_COINS}c +{REWARD_FOCUS_XP}XP")
            # decide next break
            if self.completed_focus_in_cycle >= self.opts.get("long_after_n_focus",2):
                self.completed_focus_in_cycle = 0
                self.after(1500, self.start_long)
            else:
                self.after(1500, self.start_short)
        else:
            play_beep("ok", self)
            self.status.config(text="Break finished. Ready for next focus.")

# ---------- Tasks tab

class TasksTab(ttk.Frame):
    def __init__(self, master, stats_refresh_cb):
        super().__init__(master)
        self.stats_refresh_cb = stats_refresh_cb
        top = ttk.Frame(self); top.pack(fill="x", pady=4)
        ttk.Label(top, text="Tasks & Subtasks (weighted)", font=("Segoe UI", 12, "bold")).pack(side="left", padx=6)
        ttk.Button(top, text="New Task", command=self.add_task).pack(side="right", padx=6)

        self.tree = ttk.Treeview(self, columns=("weight","done"), show="tree headings", selectmode="browse")
        self.tree.heading("#0", text="Title")
        self.tree.heading("weight", text="Weight %")
        self.tree.heading("done", text="Done?")
        self.tree.column("weight", width=80, anchor="center")
        self.tree.column("done", width=60, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=6, pady=(0,6))

        btns = ttk.Frame(self); btns.pack(fill="x", pady=4)
        ttk.Button(btns, text="Add Subtask", command=self.add_subtask).pack(side="left", padx=4)
        ttk.Button(btns, text="Toggle Done", command=self.toggle_done).pack(side="left", padx=4)
        ttk.Button(btns, text="Set Weight", command=self.set_weight).pack(side="left", padx=4)
        ttk.Button(btns, text="Delete", command=self.delete_item).pack(side="left", padx=4)

        self.progress = ttk.Progressbar(self, orient="horizontal", mode="determinate", length=400)
        self.progress.pack(pady=6)

        self.refresh_tree()

    def _data(self):
        return load()

    def _save(self, state):
        save(state)

    def refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        s = self._data()
        for t in s.get("tasks", []):
            tid = f"t:{t['id']}"
            self.tree.insert("", "end", iid=tid, text=t["title"], values=("", ""))
            # subtasks
            for sub in t.get("subtasks", []):
                self.tree.insert(tid, "end",
                                 iid=f"s:{t['id']}:{sub['id']}",
                                 text=sub["title"],
                                 values=(sub["weight"], "✓" if sub["done"] else ""))
            # update progress bar for selected task
        self.update_progress()

    def _selected_task(self):
        sel = self.tree.selection()
        if not sel: return None
        iid = sel[0]
        if iid.startswith("t:"):
            return iid.split(":")[1]
        elif iid.startswith("s:"):
            return iid.split(":")[1]
        return None

    def _selected_is_subtask(self):
        sel = self.tree.selection()
        return bool(sel and sel[0].startswith("s:"))

    def add_task(self):
        title = simpledialog.askstring("New Task", "Task title:")
        if not title: return
        s = self._data()
        t_id = random.randint(1000, 999999)
        s["tasks"].append({"id": t_id, "title": title, "subtasks": []})
        self._save(s)
        self.refresh_tree()

    def add_subtask(self):
        task_id = self._selected_task()
        if not task_id:
            messagebox.showinfo("Pick a task", "Select a task to add a subtask.")
            return
        title = simpledialog.askstring("New Subtask", "Subtask title:")
        if not title: return
        weight = simpledialog.askinteger("Weight %", "Enter weight (0-100):", minvalue=0, maxvalue=100)
        if weight is None: return
        s = self._data()
        for t in s["tasks"]:
            if str(t["id"]) == str(task_id):
                sub_id = random.randint(1000, 999999)
                t["subtasks"].append({"id": sub_id, "title": title, "weight": int(weight), "done": False})
                # validate weights sum
                total = sum(x["weight"] for x in t["subtasks"])
                if total != 100:
                    messagebox.showwarning("Weights", f"Current total weight = {total}%. Aim for 100%.")
        self._save(s)
        self.refresh_tree()

    def set_weight(self):
        if not self._selected_is_subtask():
            messagebox.showinfo("Select subtask", "Select a subtask to set weight.")
            return
        sel = self.tree.selection()[0]
        _, task_id, sub_id = sel.split(":")
        new_w = simpledialog.askinteger("Weight %", "Enter weight (0-100):", minvalue=0, maxvalue=100)
        if new_w is None: return
        s = self._data()
        for t in s["tasks"]:
            if str(t["id"]) == task_id:
                for sub in t["subtasks"]:
                    if str(sub["id"]) == sub_id:
                        sub["weight"] = int(new_w)
        self._save(s)
        self.refresh_tree()

    def toggle_done(self):
        if not self._selected_is_subtask():
            messagebox.showinfo("Select subtask", "Select a subtask to toggle done.")
            return
        sel = self.tree.selection()[0]
        _, task_id, sub_id = sel.split(":")
        s = self._data()
        for t in s["tasks"]:
            if str(t["id"]) == task_id:
                for sub in t["subtasks"]:
                    if str(sub["id"]) == sub_id:
                        sub["done"] = not sub["done"]
                        if sub["done"]:
                            # proportional reward
                            c = int(sub["weight"] * REWARD_SUBTASK_COINS_PER_PCT)
                            x = int(sub["weight"] * REWARD_SUBTASK_XP_PER_PCT)
                            reward(c, x, 0)
                            self.stats_refresh_cb()
        self._save(s)
        self.refresh_tree()

    def delete_item(self):
        sel = self.tree.selection()
        if not sel: return
        iid = sel[0]
        s = self._data()
        if iid.startswith("t:"):
            task_id = iid.split(":")[1]
            s["tasks"] = [t for t in s["tasks"] if str(t["id"]) != task_id]
        else:
            _, task_id, sub_id = iid.split(":")
            for t in s["tasks"]:
                if str(t["id"]) == task_id:
                    t["subtasks"] = [sub for sub in t["subtasks"] if str(sub["id"]) != sub_id]
        self._save(s)
        self.refresh_tree()

    def update_progress(self):
        """Show progress of selected task."""
        sel = self.tree.selection()
        if not sel:
            self.progress["value"] = 0
            return
        iid = sel[0]
        if iid.startswith("s:"):
            _, task_id, _ = iid.split(":")
        else:
            task_id = iid.split(":")[1]
        s = self._data()
        for t in s["tasks"]:
            if str(t["id"]) == task_id:
                done_pct = sum(sub["weight"] for sub in t["subtasks"] if sub["done"])
                self.progress["value"] = min(100, done_pct)

        self.after(300, self.update_progress)

# ---------- Calendar tab

class CalendarTab(ttk.Frame):
    COLORS = {
        "None": "#cccccc",
        "Exam": "#e74c3c",
        "Project": "#3498db",
        "Birthday": "#9b59b6",
        "Holiday": "#27ae60"
    }

    def __init__(self, master):
        super().__init__(master)
        self.today = dt.date.today()
        self.year = self.today.year
        self.month = self.today.month

        top = ttk.Frame(self); top.pack(fill="x", pady=4)
        ttk.Button(top, text="<", command=self.prev_month).pack(side="left")
        self.lbl = ttk.Label(top, text="", font=("Segoe UI", 12, "bold"))
        self.lbl.pack(side="left", padx=8)
        ttk.Button(top, text=">", command=self.next_month).pack(side="left")
        ttk.Button(top, text="Add note to date…", command=self.add_note_prompt).pack(side="right")

        self.gridf = ttk.Frame(self); self.gridf.pack(padx=6, pady=6, fill="both", expand=True)
        self.draw()

    def prev_month(self):
        d = dt.date(self.year, self.month, 1) - dt.timedelta(days=1)
        self.year, self.month = d.year, d.month
        self.draw()

    def next_month(self):
        days = calendar.monthrange(self.year, self.month)[1]
        d = dt.date(self.year, self.month, days) + dt.timedelta(days=1)
        self.year, self.month = d.year, d.month
        self.draw()

    def draw(self):
        for w in self.gridf.winfo_children(): w.destroy()
        self.lbl.config(text=f"{calendar.month_name[self.month]} {self.year}")

        head = ttk.Frame(self.gridf); head.pack(fill="x")
        for wd in ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]:
            ttk.Label(head, text=wd, width=8, anchor="center").pack(side="left", expand=True)

        s = load()
        cal = calendar.Calendar(firstweekday=0)  # Monday
        for week in cal.monthdatescalendar(self.year, self.month):
            row = ttk.Frame(self.gridf); row.pack(fill="x")
            for day in week:
                btn = ttk.Button(row, text=str(day.day), width=8)
                btn.pack(side="left", expand=True, padx=1, pady=1)
                iso = day.isoformat()
                if iso in s.get("calendar", {}):
                    color = s["calendar"][iso].get("color", "#cccccc")
                    btn.config(style="")
                    btn.configure(text=f"{day.day} •")
                    btn["command"] = lambda d=day: self.edit_note(d)
                    # quick color hint
                    btn.configure(takefocus=False)
                    btn.bind("<Expose>", lambda e, b=btn, c=color: b.configure()
                             )
                    btn.configure()
                    btn.configure()
                    btn.configure()
                    # color via style
                    style_name = f"Color.TButton.{iso}"
                    style = ttk.Style()
                    style.configure(style_name, foreground="black", background=color)
                    btn.configure(style=style_name)
                else:
                    btn["command"] = lambda d=day: self.add_note(d)

                if day.month != self.month:
                    btn.state(["disabled"])

    def add_note_prompt(self):
        d = simpledialog.askstring("Date (YYYY-MM-DD)", "Enter date:")
        if not d: return
        try:
            y,m,day = map(int, d.split("-"))
            date_obj = dt.date(y,m,day)
        except Exception:
            messagebox.showerror("Invalid", "Use YYYY-MM-DD.")
            return
        self.add_note(date_obj)

    def add_note(self, date_obj):
        title = simpledialog.askstring("Title", f"Note for {date_obj.isoformat()}:")
        if title is None: return
        color_name = simpledialog.askstring("Color", f"Pick category {list(self.COLORS.keys())}:",
                                            initialvalue="None")
        color = self.COLORS.get(color_name or "None", "#cccccc")
        note = simpledialog.askstring("Details", "Optional note:")
        s = load()
        s.setdefault("calendar", {})
        s["calendar"][date_obj.isoformat()] = {"title": title, "color": color, "note": note or ""}
        save(s)
        self.draw()

    def edit_note(self, date_obj):
        s = load()
        key = date_obj.isoformat()
        data = s["calendar"].get(key, {})
        title = simpledialog.askstring("Edit Title", "Title:", initialvalue=data.get("title",""))
        if title is None: return
        _, color_hex = colorchooser.askcolor(title="Pick color", color=data.get("color","#cccccc"))
        note = simpledialog.askstring("Edit Note", "Note:", initialvalue=data.get("note",""))
        s["calendar"][key] = {"title": title, "color": color_hex or "#cccccc", "note": note or ""}
        save(s)
        self.draw()

# ---------- Reports tab

class ReportsTab(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        top = ttk.Frame(self); top.pack(fill="x", pady=4)
        ttk.Label(top, text="Reports", font=("Segoe UI", 12, "bold")).pack(side="left", padx=6)
        ttk.Button(top, text="Today", command=self.show_today).pack(side="left", padx=4)
        ttk.Button(top, text="This Week", command=self.show_week).pack(side="left", padx=4)
        ttk.Button(top, text="Custom…", command=self.show_custom).pack(side="left", padx=4)

        self.info = tk.Text(self, height=10)
        self.info.pack(fill="x", padx=6, pady=6)

        self.daily_frame = ttk.Frame(self); self.daily_frame.pack(fill="x", padx=6, pady=(0,6))
        self.show_week()  # default

    def _range(self, start_dt, end_dt):
        # aggregate by day
        s = load()
        sessions = s.get("sessions", [])
        by_day = {}
        total_focus = total_break = 0
        for sess in sessions:
            st = dt.datetime.fromtimestamp(sess["start_ts"])
            if not (start_dt <= st <= end_dt): continue
            dur = max(0, sess["end_ts"] - sess["start_ts"])
            day_key = st.date().isoformat()
            by_day.setdefault(day_key, {"FOCUS":0,"SHORT":0,"LONG":0})
            by_day[day_key][sess["type"]] += dur
            if sess["type"] == "FOCUS": total_focus += dur
            else: total_break += dur

        self.info.delete("1.0", "end")
        self.info.insert("end", f"From {start_dt.date()} to {end_dt.date()}\n")
        self.info.insert("end", f"Total Focus: {total_focus//60} min\n")
        self.info.insert("end", f"Total Breaks: {total_break//60} min\n")
        self.info.insert("end", f"Sessions completed: {load()['sessions_completed']}\n")

        for w in self.daily_frame.winfo_children(): w.destroy()
        # simple per-day bars
        for k in sorted(by_day.keys()):
            row = ttk.Frame(self.daily_frame); row.pack(fill="x", pady=2)
            ttk.Label(row, text=k, width=12).pack(side="left")
            foc = by_day[k]["FOCUS"]//60
            brk = (by_day[k]["SHORT"]+by_day[k]["LONG"])//60
            pb1 = ttk.Progressbar(row, length=240, maximum=240, value=min(240, foc))
            pb1.pack(side="left", padx=4)
            ttk.Label(row, text=f"{foc}m focus").pack(side="left", padx=6)
            pb2 = ttk.Progressbar(row, length=160, maximum=160, value=min(160, brk))
            pb2.pack(side="left", padx=4)
            ttk.Label(row, text=f"{brk}m break").pack(side="left", padx=6)

    def show_today(self):
        now = dt.datetime.now()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        self._range(start, now)

    def show_week(self):
        now = dt.datetime.now()
        start = now - dt.timedelta(days=6)
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        self._range(start, now)

    def show_custom(self):
        a = simpledialog.askstring("Start (YYYY-MM-DD)", "Start date:")
        b = simpledialog.askstring("End (YYYY-MM-DD)", "End date:")
        try:
            s = dt.datetime.fromisoformat(a+" 00:00:00")
            e = dt.datetime.fromisoformat(b+" 23:59:59")
        except Exception:
            messagebox.showerror("Invalid", "Please use YYYY-MM-DD")
            return
        self._range(s, e)

# ---------- Stats bar & game launcher

class StatsBar(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.pack(fill="x")
        self.coins_lbl = ttk.Label(self, text="Coins: 0"); self.coins_lbl.pack(side="left", padx=8)
        self.xp_lbl = ttk.Label(self, text="XP: 0"); self.xp_lbl.pack(side="left", padx=8)
        self.sess_lbl = ttk.Label(self, text="Sessions: 0"); self.sess_lbl.pack(side="left", padx=8)
        ttk.Button(self, text="Open Reward World", command=self.open_game).pack(side="right", padx=6)
        self.refresh()
        self.after(3000, self._tick)

    def _tick(self):
        self.refresh()
        self.after(3000, self._tick)

    def refresh(self):
        s = load()
        self.coins_lbl.config(text=f"Coins: {s['coins']}")
        self.xp_lbl.config(text=f"XP: {s['xp']}")
        self.sess_lbl.config(text=f"Sessions: {s['sessions_completed']}")

    def open_game(self):
        here = os.path.dirname(__file__)
        game = os.path.join(here, "pg_game.py")
        subprocess.Popen([sys.executable, game])

# ---------- App shell

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("820x640")
        self.style = ttk.Style(self)
        self.style.theme_use("default")

        self.stats = StatsBar(self)

        nb = ttk.Notebook(self); nb.pack(fill="both", expand=True)
        self.tab_timer = PomodoroTab(nb, stats_refresh_cb=self.stats.refresh)
        self.tab_tasks = TasksTab(nb, stats_refresh_cb=self.stats.refresh)
        self.tab_calendar = CalendarTab(nb)
        self.tab_reports = ReportsTab(nb)

        nb.add(self.tab_timer, text="Timer")
        nb.add(self.tab_tasks, text="Tasks")
        nb.add(self.tab_calendar, text="Calendar")
        nb.add(self.tab_reports, text="Reports")

def main():
    App().mainloop()

if __name__ == "__main__":
    main()
