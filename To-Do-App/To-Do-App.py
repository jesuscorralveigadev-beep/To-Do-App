import sqlite3
import csv
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
from datetime import datetime
from pathlib import Path

# Database file
DB_NAME = "todo.db"
ASSETS_DIR = Path(__file__).parent / "todo_portfolio_assets"

# Safe ORDER BY mapping
ORDER_MAP = {
    "priority,created_at": "priority DESC, created_at DESC",
    "created_at": "created_at DESC",
    "priority": "priority DESC"
}

# ---------------- Database layer ----------------

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS TODO (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            completed INTEGER DEFAULT 0,
            created_at TEXT,
            due_date TEXT,
            priority INTEGER DEFAULT 2
        )
    """)
    conn.commit()
    conn.close()

def add_task(name, description, due_date, priority):
    created_at = datetime.utcnow().isoformat(timespec='seconds')
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO TODO (name, description, completed, created_at, due_date, priority) VALUES (?, ?, 0, ?, ?, ?)",
        (name, description, created_at, due_date if due_date else None, int(priority))
    )
    conn.commit()
    conn.close()

def get_tasks(filter_text="", order_by="priority DESC, created_at DESC"):
    conn = get_connection()
    cur = conn.cursor()
    if filter_text:
        like = f"%{filter_text}%"
        cur.execute(
            f"SELECT id, name, description, completed, created_at, due_date, priority FROM TODO WHERE name LIKE ? OR description LIKE ? ORDER BY {order_by}",
            (like, like)
        )
    else:
        cur.execute(f"SELECT id, name, description, completed, created_at, due_date, priority FROM TODO ORDER BY {order_by}")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_task_by_id(task_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, description, completed, created_at, due_date, priority FROM TODO WHERE id = ?", (task_id,))
    row = cur.fetchone()
    conn.close()
    return row

def update_task(task_id, name, description, due_date, priority):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE TODO SET name = ?, description = ?, due_date = ?, priority = ? WHERE id = ?",
        (name, description, due_date if due_date else None, int(priority), task_id)
    )
    conn.commit()
    conn.close()

def delete_task(task_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM TODO WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

def toggle_completed(task_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE TODO SET completed = CASE WHEN completed=0 THEN 1 ELSE 0 END WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

def export_tasks_to_csv(filepath):
    tasks = get_tasks("")
    try:
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(['id','name','description','completed','created_at','due_date','priority'])
            for t in tasks:
                writer.writerow(list(t))
        return True, f"Exported {len(tasks)} tasks to {filepath}"
    except Exception as e:
        return False, str(e)

# ---------------- Visual palettes & helpers ----------------

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# Light and dark palettes (Frutiger Aero inspired)
LIGHT = {
    "window_bg": "#eaf2ff",
    "glass": "#f7fbff",
    "panel": "#f5f9ff",
    "card": "#e1edff",
    "card_inner_stroke": "#ffffff",
    "text": "#06234a",
    "muted": "#58606b"
}

DARK = {
    "window_bg": "#07101c",
    "glass": "#071826",
    "panel": "#0f1724",
    "card": "#102230",
    "card_inner_stroke": "#0b1220",
    "text": "#e6eef9",
    "muted": "#9aa4b2"
}

# Priority colors per theme (1 high, 2 medium, 3 low)
PRIORITY_LIGHT = {1: "#fff1f0", 2: "#fff8e6", 3: "#effaf1"}
PRIORITY_DARK  = {1: "#4c1111", 2: "#664900", 3: "#0f5132"}

# Optional icon loader
def load_icon_png(name):
    path = ASSETS_DIR / f"{name}.png"
    if path.exists():
        try:
            return tk.PhotoImage(file=str(path))
        except Exception:
            return None
    return None

# A small safe color-apply helper
def safe_configure(widget, **kwargs):
    try:
        widget.configure(**kwargs)
    except Exception:
        pass

# Centralized helpers for theme/priorities
def get_priority_bg(priority, is_dark):
    try:
        p = int(priority)
    except Exception:
        p = 2
    return PRIORITY_DARK.get(p, DARK["card"]) if is_dark else PRIORITY_LIGHT.get(p, LIGHT["card"])

def theme_text_color(is_dark):
    return DARK["text"] if is_dark else LIGHT["text"]

def theme_muted_color(is_dark):
    return DARK["muted"] if is_dark else LIGHT["muted"]

# ---------------- App ----------------

class ToDoApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Frutiger Aero To-Do")
        self.geometry("980x620")
        self.minsize(900, 520)

        # icons (optional)
        self.icon_check = load_icon_png("check")
        self.icon_trash = load_icon_png("trash")
        self.icon_calendar = load_icon_png("calendar")

        # state
        self.selected_task_id = None
        self.task_card_widgets = []  # list of tuples (id, frame)
        self.pulse_after_id = None

        # theming toggle
        self.dark_mode_var = tk.BooleanVar(value=False)

        # build UI
        self.build_ui()

        # DB init and initial load
        init_db()
        self.apply_theme(LIGHT)  # start light
        self.refresh_tasks()

    # ---------- UI construction ----------
    def build_ui(self):
        # root glass container
        self.root_frame = ctk.CTkFrame(self, fg_color=LIGHT["window_bg"])
        self.root_frame.pack(fill="both", expand=True, padx=12, pady=12)

        # Header
        header = ctk.CTkFrame(self.root_frame, fg_color="transparent")
        header.pack(fill="x", pady=(6,8))

        # Title (text color will be updated by apply_theme)
        self.title_label = ctk.CTkLabel(header, text="To-Do", font=ctk.CTkFont(size=20, weight="bold"))
        self.title_label.pack(side="left", padx=(6,12))

        # search
        self.search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(header, placeholder_text="Search tasks...", textvariable=self.search_var, width=360)
        search_entry.pack(side="left", padx=(0,8))
        search_entry.bind("<KeyRelease>", lambda e: self.refresh_tasks())

        # order option menu
        self.order_var = tk.StringVar(value="priority,created_at")
        order_menu = ctk.CTkOptionMenu(header, values=list(ORDER_MAP.keys()), variable=self.order_var, command=lambda v: self.refresh_tasks())
        order_menu.pack(side="left", padx=(6,8))
        order_menu.set("priority,created_at")

        # refresh button
        refresh_btn = ctk.CTkButton(header, text="Refresh", command=self.refresh_tasks, width=90)
        refresh_btn.pack(side="left", padx=(0,8))

        # theme switch
        theme_switch = ctk.CTkSwitch(header, text="Dark mode", command=self.toggle_dark_mode, variable=self.dark_mode_var)
        theme_switch.pack(side="right", padx=(8,6))

        # Export CSV button
        export_btn = ctk.CTkButton(header, text="Export CSV", command=self.export_csv_dialog, width=110)
        export_btn.pack(side="right")

        # Main content: left list + right details
        main_container = ctk.CTkFrame(self.root_frame, fg_color="transparent")
        main_container.pack(fill="both", expand=True)

        # LEFT: list + add form
        self.left_panel = ctk.CTkFrame(main_container, fg_color=LIGHT["panel"], corner_radius=12)
        self.left_panel.pack(side="left", fill="both", expand=True, padx=(0,10), pady=6)

        # Add form
        form = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        form.pack(fill="x", padx=12, pady=12)

        self.label_taskname = ctk.CTkLabel(form, text="Task name")
        self.label_taskname.grid(row=0, column=0, sticky="w", padx=6, pady=(2,6))
        self.entry_name = ctk.CTkEntry(form, width=360)
        self.entry_name.grid(row=0, column=1, padx=6, pady=(2,6))

        self.label_desc = ctk.CTkLabel(form, text="Description")
        self.label_desc.grid(row=1, column=0, sticky="w", padx=6, pady=6)
        self.entry_desc = ctk.CTkEntry(form, width=360)
        self.entry_desc.grid(row=1, column=1, padx=6, pady=6)

        self.label_due = ctk.CTkLabel(form, text="Due date (YYYY-MM-DD)")
        self.label_due.grid(row=2, column=0, sticky="w", padx=6, pady=6)
        self.entry_due = ctk.CTkEntry(form, width=160)
        self.entry_due.grid(row=2, column=1, sticky="w", padx=6, pady=6)

        self.label_priority = ctk.CTkLabel(form, text="Priority")
        self.label_priority.grid(row=0, column=2, sticky="w", padx=10, pady=(2,6))
        self.priority_opt = ctk.CTkOptionMenu(form, values=["1 - High", "2 - Medium", "3 - Low"])
        self.priority_opt.set("2 - Medium")
        self.priority_opt.grid(row=0, column=3, padx=6, pady=(2,6))

        add_btn = ctk.CTkButton(form, text="Add Task", command=self.add_task_from_form, width=120)
        add_btn.grid(row=1, column=3, padx=6, pady=6)

        # Separator
        ctk.CTkFrame(self.left_panel, height=1, fg_color="#dfeaff").pack(fill="x", padx=12, pady=(6,8))

        # Scrollable task list
        self.task_frame = ctk.CTkScrollableFrame(self.left_panel, fg_color="transparent", corner_radius=8)
        self.task_frame.pack(fill="both", expand=True, padx=12, pady=8)

        # RIGHT: details panel
        self.right_panel = ctk.CTkFrame(main_container, fg_color=LIGHT["glass"], corner_radius=12, width=320)
        self.right_panel.pack(side="right", fill="y", padx=(10,0), pady=6)

        self.details_title = ctk.CTkLabel(self.right_panel, text="Task details", font=ctk.CTkFont(size=16, weight="bold"))
        self.details_title.pack(pady=(12,6), anchor="w", padx=12)

        self.details_name = ctk.CTkEntry(self.right_panel, placeholder_text="Task name")
        self.details_name.pack(fill="x", padx=12, pady=6)

        self.details_desc = ctk.CTkTextbox(self.right_panel, height=160)
        self.details_desc.pack(fill="x", padx=12, pady=6)

        meta_row = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        meta_row.pack(fill="x", padx=12, pady=(0,6))

        self.details_due = ctk.CTkEntry(meta_row, placeholder_text="Due date (YYYY-MM-DD)")
        self.details_due.pack(side="left", fill="x", expand=True, padx=(0,8))

        self.details_priority = ctk.CTkOptionMenu(meta_row, values=["1 - High", "2 - Medium", "3 - Low"])
        self.details_priority.set("2 - Medium")
        self.details_priority.pack(side="right")

        # control buttons
        ctrl = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        ctrl.pack(pady=8)

        save_btn = ctk.CTkButton(ctrl, text="Save", width=120, command=self.save_selected_task)
        save_btn.pack(side="left", padx=8)

        if self.icon_trash:
            del_btn = ctk.CTkButton(ctrl, text="Delete", image=self.icon_trash, compound="left", fg_color="#d9534f", hover_color="#b0302a", command=self.delete_selected_task)
        else:
            del_btn = ctk.CTkButton(ctrl, text="Delete", fg_color="#d9534f", hover_color="#b0302a", command=self.delete_selected_task)
        del_btn.pack(side="left", padx=8)

        # details meta label
        self.details_meta = ctk.CTkLabel(self.right_panel, text="")
        self.details_meta.pack(padx=12, pady=(6,12), anchor="w")

    # ---------- Data actions ----------
    def add_task_from_form(self):
        name = self.entry_name.get().strip()
        if not name:
            messagebox.showwarning("Validation", "Task name is required.")
            return
        desc = self.entry_desc.get().strip()
        due = self.entry_due.get().strip()
        priority_text = self.priority_opt.get().split(" - ")[0]
        try:
            priority = int(priority_text)
        except Exception:
            priority = 2
        add_task(name, desc, due if due else None, priority)
        # clear inputs
        self.entry_name.delete(0, "end")
        self.entry_desc.delete(0, "end")
        self.entry_due.delete(0, "end")
        self.priority_opt.set("2 - Medium")
        self.refresh_tasks()

    def refresh_tasks(self):
        # clear old cards
        for w in self.task_frame.winfo_children():
            w.destroy()
        self.task_card_widgets.clear()

        filter_text = self.search_var.get().strip()

        # SAFELY map the option menu value to a valid ORDER BY clause
        order_key = self.order_var.get()
        order_by_clause = ORDER_MAP.get(order_key, ORDER_MAP["priority,created_at"])

        # pass the safe order clause to get_tasks
        tasks = get_tasks(filter_text=filter_text, order_by=order_by_clause)

        is_dark = ctk.get_appearance_mode().lower() == "dark"
        text_color = theme_text_color(is_dark)
        muted_color = theme_muted_color(is_dark)

        for t in tasks:
            tid, name, desc, completed, created_at, due_date, priority = t
            # priority from DB may be stored as int or text — ensure int
            try:
                priority = int(priority)
            except Exception:
                priority = 2

            bg = get_priority_bg(priority, is_dark)

            card = ctk.CTkFrame(self.task_frame, fg_color=bg, corner_radius=12)
            card.pack(fill="x", pady=8, padx=8)
            # store ref for theme updates/animations
            self.task_card_widgets.append((tid, card))

            # left: text
            title_text = f"{name}"
            if completed:
                title_text = f"[COMPLETED] {title_text}"
            lbl_title = ctk.CTkLabel(card, text=title_text, anchor="w", text_color=text_color, font=ctk.CTkFont(size=13, weight="bold"))
            lbl_title.grid(row=0, column=0, sticky="w", padx=12, pady=(8,2))

            meta = f"Priority: {priority}   •   Created: {created_at}"
            if due_date:
                meta += f"   •   Due: {due_date}"
            lbl_meta = ctk.CTkLabel(card, text=meta, anchor="w", text_color=muted_color, font=ctk.CTkFont(size=10))
            lbl_meta.grid(row=1, column=0, sticky="w", padx=12, pady=(0,8))

            # right: buttons
            btns = ctk.CTkFrame(card, fg_color="transparent")
            btns.grid(row=0, column=1, rowspan=2, sticky="e", padx=8, pady=6)

            # view/edit button selects the task and shows details
            view_btn = ctk.CTkButton(btns, text="View", width=100, command=lambda id=tid: self.on_task_selected(id))
            view_btn.pack(side="top", pady=(4,4))

            # complete button
            comp_text = "Mark Undone" if completed else "Mark Done"
            comp_btn = ctk.CTkButton(btns, text=comp_text, width=120, command=lambda id=tid: self.toggle_complete_and_reload(id))
            comp_btn.pack(side="top", pady=(4,4))

            # delete small button
            del_btn = ctk.CTkButton(btns, text="Delete", width=100, fg_color="#c44", hover_color="#a33", command=lambda id=tid: self.delete_and_reload(id))
            del_btn.pack(side="top", pady=(4,8))

            # hover bindings for lightweight hover effect
            self._bind_hover(card, bg)

        # if a task was previously selected, re-show it if still present
        if self.selected_task_id:
            if get_task_by_id(self.selected_task_id):
                self.on_task_selected(self.selected_task_id)
            else:
                self.clear_details()

    def _bind_hover(self, widget, base_bg):
        # simple hover: on enter, set slightly lighter hover color; on leave, restore
        hover_color = "#c7ddff" if ctk.get_appearance_mode().lower() == "light" else "#163144"
        def on_enter(e):
            try:
                widget._prev_bg = widget.cget("fg_color")
            except Exception:
                widget._prev_bg = base_bg
            safe_configure(widget, fg_color=hover_color)
        def on_leave(e):
            safe_configure(widget, fg_color=getattr(widget, "_prev_bg", base_bg))
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def on_task_selected(self, task_id):
        task = get_task_by_id(task_id)
        if not task:
            return
        self.selected_task_id = task_id
        _, name, desc, completed, created_at, due_date, priority = task
        # populate details panel
        self.details_name.delete(0, "end")
        self.details_name.insert(0, name)
        self.details_desc.configure(state="normal")
        self.details_desc.delete("1.0", "end")
        self.details_desc.insert("1.0", desc or "")
        self.details_desc.configure(state="normal")
        self.details_due.delete(0, "end")
        if due_date:
            self.details_due.insert(0, due_date)
        # ensure priority is set with label "N - Label"
        try:
            p = int(priority)
        except Exception:
            p = 2
        label = f"{p} - {'High' if p==1 else 'Medium' if p==2 else 'Low'}"
        self.details_priority.set(label)
        meta = f"Created: {created_at}   •   Completed: {'Yes' if completed else 'No'}"
        self.details_meta.configure(text=meta)
        # animate selected card
        self.animate_selection(task_id)

    def save_selected_task(self):
        if not self.selected_task_id:
            messagebox.showinfo("Info", "Select a task first or use Add Task on the left to create.")
            return
        name = self.details_name.get().strip()
        if not name:
            messagebox.showwarning("Validation", "Task name is required.")
            return
        desc = self.details_desc.get("1.0", "end").strip()
        due = self.details_due.get().strip()
        # parse priority number from option menu "N - Label"
        ptext = self.details_priority.get().split(" - ")[0]
        try:
            priority = int(ptext)
        except Exception:
            priority = 2
        update_task(self.selected_task_id, name, desc, due if due else None, priority)
        messagebox.showinfo("Saved", "Task updated.")
        # DESMARCAR y limpiar panel derecho ANTES de refrescar
        self.clear_details()
        self.refresh_tasks()

    def delete_selected_task(self):
        if not self.selected_task_id:
            messagebox.showinfo("Info", "No task selected.")
            return
        if messagebox.askyesno("Confirm", "Delete selected task?"):
            delete_task(self.selected_task_id)
            self.clear_details()
            self.refresh_tasks()

    def delete_and_reload(self, task_id):
        if messagebox.askyesno("Confirm", "Delete this task?"):
            delete_task(task_id)
            if self.selected_task_id == task_id:
                self.clear_details()
            self.refresh_tasks()

    def toggle_complete_and_reload(self, task_id):
        toggle_completed(task_id)
        # Desmarcamos siempre para que no quede la tarjeta "seleccionada"
        if self.selected_task_id == task_id:
            self.clear_details()
        self.refresh_tasks()

    def clear_details(self):
        self.selected_task_id = None
        self.details_name.delete(0, "end")
        self.details_desc.configure(state="normal")
        self.details_desc.delete("1.0", "end")
        self.details_desc.configure(state="disabled")
        self.details_due.delete(0, "end")
        self.details_priority.set("2 - Medium")
        self.details_meta.configure(text="")

    # ---------- Theme control (apply theme to all) ----------
    def toggle_dark_mode(self):
        if self.dark_mode_var.get():
            ctk.set_appearance_mode("dark")
            self.apply_theme(DARK)
        else:
            ctk.set_appearance_mode("light")
            self.apply_theme(LIGHT)

    def apply_theme(self, palette):
        is_dark = palette is DARK

        # apply to main window and base frames
        safe_configure(self.root_frame, fg_color=palette["window_bg"])

        # left/right known panels
        safe_configure(self.left_panel, fg_color=palette.get("panel", palette.get("glass")))
        safe_configure(self.right_panel, fg_color=palette.get("glass"))
        safe_configure(self.task_frame, fg_color=palette.get("panel", palette.get("glass")))

        # update many textual widgets to correct text color
        text_color = theme_text_color(is_dark)
        muted = theme_muted_color(is_dark)
        try:
            safe_configure(self.title_label, text_color=text_color)
        except Exception:
            pass
        try:
            safe_configure(self.label_taskname, text_color=text_color)
            safe_configure(self.label_desc, text_color=text_color)
            safe_configure(self.label_due, text_color=text_color)
            safe_configure(self.label_priority, text_color=text_color)
            safe_configure(self.details_title, text_color=text_color)
            safe_configure(self.details_meta, text_color=muted)
        except Exception:
            pass

        # rebuild tasks so cards use correct colors for the theme
        self.refresh_tasks()

    # ---------- Small animations ----------
    def animate_selection(self, task_id):
        # cancel previous pulse
        if self.pulse_after_id:
            self.after_cancel(self.pulse_after_id)
            self.pulse_after_id = None

        # find the target card
        target = None
        for tid, widget in self.task_card_widgets:
            if tid == task_id:
                target = widget
                break
        if not target:
            return

        is_dark = ctk.get_appearance_mode().lower() == "dark"
        base = target.cget("fg_color")
        pulse_color = "#a8d1ff" if not is_dark else "#163144"
        steps = 6
        interval = 80

        def step(i=0):
            if i % 2 == 0:
                safe_configure(target, fg_color=pulse_color)
            else:
                safe_configure(target, fg_color=base)
            next_i = i + 1
            if next_i <= steps:
                self.pulse_after_id = self.after(interval, lambda: step(next_i))
            else:
                self.pulse_after_id = None

        step(0)

    # ---------- Export ----------
    def export_csv_dialog(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files","*.csv")])
        if not path:
            return
        ok, msg = export_tasks_to_csv(path)
        if ok:
            messagebox.showinfo("Export", msg)
        else:
            messagebox.showerror("Export Error", msg)

# ---------------- Run ----------------

if __name__ == "__main__":
    init_db()
    app = ToDoApp()
    app.mainloop()
