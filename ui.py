import tkinter as tk
from tkinter import ttk
from driver import DriverState


# ──────────────────────────────────────────────────────────────────────────────
# Theme / palette
# ──────────────────────────────────────────────────────────────────────────────
BG_DARK  = "#0B1A2B"
BG_CARD  = "#0F2538"
BG_MID   = "#152D42"
ACCENT   = "#F97316"        # orange
ACCENT2  = "#38BDF8"        # sky-blue
TEXT_PRI = "#F0F4F8"
TEXT_SEC = "#8BA4B8"
SUCCESS  = "#4ADE80"
WARNING  = "#FBBF24"
DANGER   = "#F87171"

DRIVER_COLORS = {
    "Idle":     "#4ADE80",
    "Moving":   "#FBBF24",
    "Dropoff":  "#38BDF8",
    "Done":     "#A78BFA",
}

EDGE_COLOR  = "#1E3A52"
ROUTE_COLOR = "#38BDF8"
NODE_NORMAL = "#1E4A6E"
NODE_SEL    = "#F97316"


def apply_style():
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TFrame",     background=BG_DARK)
    style.configure("Card.TFrame", background=BG_CARD,  relief="flat")
    style.configure("TLabel",      background=BG_DARK,  foreground=TEXT_PRI,  font=("Segoe UI", 10))
    style.configure("Card.TLabel", background=BG_CARD,  foreground=TEXT_PRI,  font=("Segoe UI", 10))
    style.configure("Dim.TLabel",  background=BG_CARD,  foreground=TEXT_SEC,  font=("Segoe UI", 9))
    style.configure("Head.TLabel", background=BG_CARD,  foreground=ACCENT,    font=("Segoe UI", 12, "bold"))
    style.configure("Stat.TLabel", background=BG_CARD,  foreground=ACCENT2,   font=("Segoe UI", 18, "bold"))
    style.configure("TCombobox",   fieldbackground=BG_MID, background=BG_MID,
                    foreground=TEXT_PRI, selectbackground=BG_MID, font=("Segoe UI", 10))
    style.configure("TRadiobutton", background=BG_CARD, foreground=TEXT_PRI,  font=("Segoe UI", 9))
    style.configure("TCheckbutton", background=BG_CARD, foreground=TEXT_PRI,  font=("Segoe UI", 9))
    style.configure("Accent.TButton",  background=ACCENT,  foreground="white",
                    font=("Segoe UI", 10, "bold"), relief="flat", padding=(12, 6))
    style.configure("Ghost.TButton",   background=BG_MID,  foreground=TEXT_PRI,
                    font=("Segoe UI", 9),  relief="flat", padding=(8, 5))
    style.map("Accent.TButton", background=[("active", "#E06010")])
    style.map("Ghost.TButton",  background=[("active", "#1E3A52")])


# ──────────────────────────────────────────────────────────────────────────────
# Reusable widgets
# ──────────────────────────────────────────────────────────────────────────────
def make_card(parent, title=None, expand=False, side=None):
    outer = tk.Frame(parent, bg=BG_CARD, bd=0, highlightthickness=1,
                     highlightbackground="#1E3A52")
    if side:
        outer.pack(side=side, fill=tk.BOTH, expand=expand, padx=6, pady=6)
    else:
        outer.pack(fill=tk.BOTH if expand else tk.X, expand=expand, padx=6, pady=6)
    if title:
        tk.Label(outer, text=title, bg=BG_CARD, fg=ACCENT,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=(12, 6))
    return outer


def separator(parent):
    tk.Frame(parent, bg="#1E3A52", height=1).pack(fill=tk.X, padx=14, pady=4)


# ──────────────────────────────────────────────────────────────────────────────
# Map canvas drawing helpers
# ──────────────────────────────────────────────────────────────────────────────
class MapCanvas:
    CITY_R    = 11
    DRIVER_R  = 8
    FONT_CITY = ("Segoe UI", 8, "bold")
    FONT_DRV  = ("Segoe UI", 7)

    def __init__(self, parent):
        self.canvas = tk.Canvas(parent, bg="#0A1620", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self._scale = 1.0
        self._ox    = 0
        self._oy    = 0
        self.canvas.bind("<MouseWheel>", self._on_zoom)
        self.canvas.bind("<Button-4>",   self._on_zoom)
        self.canvas.bind("<Button-5>",   self._on_zoom)
        self.canvas.bind("<ButtonPress-2>",   self._pan_start)
        self.canvas.bind("<B2-Motion>",        self._pan_move)
        self.canvas.bind("<ButtonPress-3>",   self._pan_start)
        self.canvas.bind("<B3-Motion>",        self._pan_move)
        self._pan_x = self._pan_y = 0

    def _world_to_screen(self, x, y):
        return x * self._scale + self._ox, y * self._scale + self._oy

    def _on_zoom(self, event):
        factor = 1.1 if (event.delta > 0 or event.num == 4) else 0.9
        self._scale *= factor
        self._ox = event.x - (event.x - self._ox) * factor
        self._oy = event.y - (event.y - self._oy) * factor

    def _pan_start(self, event):
        self._pan_x, self._pan_y = event.x, event.y

    def _pan_move(self, event):
        dx, dy = event.x - self._pan_x, event.y - self._pan_y
        self._ox += dx; self._oy += dy
        self._pan_x, self._pan_y = event.x, event.y

    # ── drawing ──────────────────────────────────────────────────────────────
    def draw(self, graph, drivers, pickup, dropoff, route_path=None):
        c = self.canvas
        c.delete("all")

        selected = {pickup, dropoff}

        # Edges
        drawn = set()
        for (u, v), km in graph.dist.items():
            if (v, u) in drawn:
                continue
            drawn.add((u, v))
            x1, y1 = self._world_to_screen(*graph.nodes[u])
            x2, y2 = self._world_to_screen(*graph.nodes[v])
            c.create_line(x1, y1, x2, y2, fill=EDGE_COLOR, width=1.5)
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            c.create_text(mx, my - 7, text=f"{km}", fill="#2A4A62",
                          font=("Segoe UI", 7))

        # Route highlight
        if route_path and len(route_path) >= 2:
            pts = []
            for city in route_path:
                pts.extend(self._world_to_screen(*graph.nodes[city]))
            c.create_line(pts, fill=ROUTE_COLOR, width=4, smooth=False, tags="route")

        # City nodes
        r = self.CITY_R
        for city, (wx, wy) in graph.nodes.items():
            sx, sy = self._world_to_screen(wx, wy)
            is_sel = city in selected
            color  = NODE_SEL if is_sel else NODE_NORMAL
            ring   = ACCENT   if is_sel else ACCENT2
            c.create_oval(sx-r-2, sy-r-2, sx+r+2, sy+r+2, fill=ring, outline="")
            c.create_oval(sx-r,   sy-r,   sx+r,   sy+r,   fill=color, outline=ring, width=2)
            c.create_text(sx, sy, text=city[0], fill="white", font=("Segoe UI", 8, "bold"))
            c.create_text(sx, sy + r + 8, text=city,
                          fill=ACCENT if is_sel else TEXT_SEC,
                          font=self.FONT_CITY)

        # Pickup / dropoff labels
        for label, city, col in [("P", pickup, SUCCESS), ("D", dropoff, DANGER)]:
            if city in graph.nodes:
                sx, sy = self._world_to_screen(*graph.nodes[city])
                c.create_oval(sx+r-2, sy-r-8, sx+r+14, sy-r+6,
                              fill=col, outline="")
                c.create_text(sx+r+6, sy-r-1, text=label,
                              fill="white", font=("Segoe UI", 7, "bold"))

        # Drivers
        dr = self.DRIVER_R
        for driver in drivers:
            if driver.city not in graph.nodes:
                continue
            wx, wy = graph.nodes[driver.city]
            sx, sy = self._world_to_screen(wx + 4, wy - 4)
            col = driver.color
            c.create_oval(sx-dr, sy-dr, sx+dr, sy+dr,
                          fill=col, outline="white", width=1.5)
            c.create_text(sx, sy, text=driver.name[0],
                          fill="white", font=("Segoe UI", 7, "bold"))
            c.create_text(sx, sy - dr - 6, text=driver.name.split()[0],
                          fill=col, font=self.FONT_DRV)


# ──────────────────────────────────────────────────────────────────────────────
# Event log
# ──────────────────────────────────────────────────────────────────────────────
class EventLog:
    COLORS = {
        "info":    TEXT_SEC,
        "ok":      SUCCESS,
        "warn":    WARNING,
        "error":   DANGER,
        "success": SUCCESS,
        "book":    ACCENT2,
    }

    def __init__(self, parent):
        frame = make_card(parent, "📟 Event Log", expand=True)
        inner = tk.Frame(frame, bg=BG_CARD)
        inner.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        self.text = tk.Text(inner, wrap=tk.WORD, bg="#07111D", fg=TEXT_SEC,
                            font=("Consolas", 9), relief="flat",
                            state=tk.DISABLED, insertbackground=TEXT_PRI,
                            hight=12)
        scroll = tk.Scrollbar(inner, command=self.text.yview, bg=BG_MID,
                              troughcolor=BG_CARD, highlightthickness=0)
        self.text.configure(yscrollcommand=scroll.set)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        ttk.Button(frame, text="Clear", command=self.clear,
                   style="Ghost.TButton").pack(pady=(0, 8))

    def log(self, msg, typ="info"):
        from datetime import datetime
        ts  = datetime.now().strftime("[%H:%M:%S]")
        col = self.COLORS.get(typ, TEXT_SEC)
        self.text.configure(state=tk.NORMAL)
        tag = f"t{id(msg)}"
        self.text.insert(tk.END, f"{ts} {msg}\n", tag)
        self.text.tag_config(tag, foreground=col)
        self.text.configure(state=tk.DISABLED)
        self.text.see(tk.END)

    def clear(self):
        self.text.configure(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)
        self.text.configure(state=tk.DISABLED)


# ──────────────────────────────────────────────────────────────────────────────
# Driver status panel
# ──────────────────────────────────────────────────────────────────────────────
class DriverPanel:
    def __init__(self, parent):
        self.card = make_card(parent, "🚗 Drivers", expand=False)
        self.rows = {}

    def refresh(self, drivers, graph, pickup):
        from routing import compute_eta_minutes
        for w in self.card.winfo_children()[1:]:  # skip header
            w.destroy()
        self.rows = {}

        for d in drivers:
            eta = compute_eta_minutes(graph, d.city, pickup) if d.is_available else None
            bg = BG_MID if not d.is_available else BG_CARD
            row = tk.Frame(self.card, bg=bg, pady=4)
            row.pack(fill=tk.X, padx=8, pady=2)

            dot = tk.Label(row, text="●", bg=bg, fg=d.color,
                           font=("Segoe UI", 12))
            dot.pack(side=tk.LEFT, padx=(6, 4))

            info = tk.Frame(row, bg=bg)
            info.pack(side=tk.LEFT, fill=tk.X, expand=True)
            tk.Label(info, text=d.name, bg=bg, fg=TEXT_PRI,
                     font=("Segoe UI", 9, "bold")).pack(anchor="w")
            tk.Label(info, text=d.status_text, bg=bg, fg=TEXT_SEC,
                     font=("Segoe UI", 8)).pack(anchor="w")

            right = tk.Frame(row, bg=bg)
            right.pack(side=tk.RIGHT, padx=6)
            if eta is not None:
                tk.Label(right, text=f"{eta:.0f} min", bg=bg,
                         fg=WARNING, font=("Segoe UI", 9, "bold")).pack()
            tk.Label(right, text=f"⭐{d.rating:.1f}  {d.trips_completed} trips",
                     bg=bg, fg=TEXT_SEC, font=("Segoe UI", 8)).pack()

            self.rows[d.name] = row


# ──────────────────────────────────────────────────────────────────────────────
# Ride history panel
# ──────────────────────────────────────────────────────────────────────────────
class HistoryPanel:
    def __init__(self, parent):
        card = make_card(parent, "📜 Ride History", expand=False)
        self.lb = tk.Listbox(card, height=6, bg="#07111D", fg=TEXT_PRI,
                             font=("Consolas", 8), relief="flat",
                             selectbackground=BG_MID, selectforeground=ACCENT2)
        self.lb.pack(fill=tk.BOTH, padx=8, pady=(0, 8))

    def add(self, booking):
        t = booking.timestamp.strftime("%H:%M")
        line = (f"{t}  {booking.booking_id}  "
                f"{booking.pickup[:3]}→{booking.dropoff[:3]}  "
                f"₹{booking.fare}  {booking.preference[:4]}")
        self.lb.insert(0, line)
        if self.lb.size() > 30:
            self.lb.delete(tk.END)