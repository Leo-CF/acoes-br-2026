import math
import threading
import tkinter as tk
import winsound

import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

MODES = {"foco": 25 * 60, "curta": 5 * 60, "longa": 15 * 60}

C = {
    "bg":           "#0e1117",
    "card":         "#161b22",
    "tomato":       "#e63946",
    "tomato_dark":  "#b52030",
    "tomato_light": "#ff8593",
    "tomato_pale":  "#ffb3bb",
    "shadow":       "#2a0a0a",
    "leaf":         "#2dc653",
    "leaf_dark":    "#1a7a35",
    "stem":         "#2d6a4f",
    "fg":           "#ffffff",
    "hint":         "#6b7280",
    "red":          "#e63946",
    "red_hover":    "#c0392b",
    "neutral":      "#1e222a",
    "neutral_hov":  "#2e3340",
}

CX, CY, R = 160, 158, 108


class PomodoroApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Pomodoro")
        self.resizable(False, False)
        self.configure(fg_color=C["bg"])

        self._mode = "foco"
        self._time_left = MODES["foco"]
        self._running = False
        self._job = None

        self._build_mode_bar()
        self._build_canvas()
        self._build_controls()
        self._redraw()

    # ------------------------------------------------------------------
    def _build_mode_bar(self):
        f = ctk.CTkFrame(self, fg_color="transparent")
        f.pack(pady=(16, 4))

        self._mode_btns = {}
        for label, key in [("Foco", "foco"), ("Pausa Curta", "curta"), ("Pausa Longa", "longa")]:
            b = ctk.CTkButton(
                f, text=label,
                font=ctk.CTkFont("Segoe UI", 12),
                width=104, height=30, corner_radius=8,
                fg_color=C["red"] if key == "foco" else C["neutral"],
                hover_color=C["red_hover"] if key == "foco" else C["neutral_hov"],
                command=lambda k=key: self._set_mode(k),
            )
            b.pack(side="left", padx=4)
            self._mode_btns[key] = b

    def _build_canvas(self):
        self._cv = tk.Canvas(
            self, width=320, height=318,
            bg=C["bg"], highlightthickness=0,
        )
        self._cv.pack()

    def _build_controls(self):
        f = ctk.CTkFrame(self, fg_color="transparent")
        f.pack(pady=(2, 6))

        ctk.CTkButton(
            f, text="−",
            font=ctk.CTkFont(size=20, weight="bold"),
            width=46, height=46, corner_radius=23,
            fg_color=C["neutral"], hover_color=C["neutral_hov"],
            command=self._decrease,
        ).pack(side="left", padx=6)

        self._start_btn = ctk.CTkButton(
            f, text="▶  Iniciar",
            font=ctk.CTkFont("Segoe UI", 14, weight="bold"),
            width=136, height=46, corner_radius=23,
            fg_color=C["red"], hover_color=C["red_hover"],
            command=self._toggle,
        )
        self._start_btn.pack(side="left", padx=6)

        ctk.CTkButton(
            f, text="+",
            font=ctk.CTkFont(size=20, weight="bold"),
            width=46, height=46, corner_radius=23,
            fg_color=C["neutral"], hover_color=C["neutral_hov"],
            command=self._increase,
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            self, text="⟳  Reiniciar",
            font=ctk.CTkFont("Segoe UI", 12),
            width=110, height=32, corner_radius=8,
            fg_color=C["neutral"], hover_color=C["neutral_hov"],
            command=self._reset,
        ).pack(pady=(0, 18))

    # ------------------------------------------------------------------
    def _redraw(self):
        self._cv.delete("all")
        self._draw_tomato()
        self._draw_time()

    def _draw_tomato(self):
        cv = self._cv
        cx, cy, r = CX, CY, R

        # Drop shadow
        cv.create_oval(cx - r + 10, cy - r + 30,
                       cx + r + 10, cy + r + 10,
                       fill=C["shadow"], outline="")

        # Body
        cv.create_oval(cx - r, cy - r + 20,
                       cx + r, cy + r,
                       fill=C["tomato"], outline="")

        # Bottom shade (chord arc)
        cv.create_arc(cx - r, cy - r + 20, cx + r, cy + r,
                      start=210, extent=120,
                      fill=C["tomato_dark"], outline="", style="chord")

        # Shine 1
        cv.create_oval(cx - r * 0.58, cy - r * 0.32,
                       cx - r * 0.12, cy + r * 0.12,
                       fill=C["tomato_light"], outline="")

        # Shine 2 (inner glint)
        cv.create_oval(cx - r * 0.46, cy - r * 0.22,
                       cx - r * 0.20, cy - r * 0.02,
                       fill=C["tomato_pale"], outline="")

        # Stem
        cv.create_rectangle(cx - 5, cy - r + 8,
                             cx + 5, cy - r + 22,
                             fill=C["stem"], outline="")

        # Leaves (5 leaves fanned out)
        for angle in (-70, -35, 0, 35, 70):
            self._draw_leaf(cv, cx, cy - r + 20, angle)

    def _draw_leaf(self, cv, bx, by, angle_deg):
        angle = math.radians(angle_deg - 90)
        perp  = angle + math.pi / 2
        length, width = 40, 13

        tip_x = bx + length * math.cos(angle)
        tip_y = by + length * math.sin(angle)
        mx    = bx + length * 0.5 * math.cos(angle)
        my    = by + length * 0.5 * math.sin(angle)
        lx    = mx + width * math.cos(perp)
        ly    = my + width * math.sin(perp)
        rx    = mx - width * math.cos(perp)
        ry    = my - width * math.sin(perp)

        cv.create_polygon(
            bx, by, lx, ly, tip_x, tip_y, rx, ry,
            fill=C["leaf"], outline=C["leaf_dark"],
            width=1, smooth=True,
        )

    def _draw_time(self):
        mins, secs = divmod(self._time_left, 60)
        text = f"{mins:02d}:{secs:02d}"

        # Soft shadow
        self._cv.create_text(CX + 2, CY + 12 + 2, text=text,
                             font=("Segoe UI", 42, "bold"),
                             fill="#550000")
        # Main text
        self._cv.create_text(CX, CY + 12, text=text,
                             font=("Segoe UI", 42, "bold"),
                             fill="white")

    # ------------------------------------------------------------------
    def _tick(self):
        if self._time_left > 0:
            self._time_left -= 1
            self._redraw()
            self._job = self.after(1000, self._tick)
        else:
            self._running = False
            self._start_btn.configure(text="▶  Iniciar")
            self._show_done()

    def _show_done(self):
        self._cv.delete("all")
        self._draw_tomato()
        self._cv.create_text(CX + 2, CY + 12 + 2, text="✓ Pronto!",
                             font=("Segoe UI", 34, "bold"), fill="#003300")
        self._cv.create_text(CX, CY + 12, text="✓ Pronto!",
                             font=("Segoe UI", 34, "bold"), fill=C["leaf"])
        threading.Thread(target=self._play_done_sound, daemon=True).start()

    def _play_done_sound(self):
        for freq, dur in [(523, 150), (659, 150), (784, 300)]:
            winsound.Beep(freq, dur)

    def _toggle(self):
        if self._running:
            self._running = False
            if self._job:
                self.after_cancel(self._job)
            self._start_btn.configure(text="▶  Continuar")
        else:
            self._running = True
            self._start_btn.configure(text="⏸  Pausar")
            self._tick()

    def _reset(self):
        if self._job:
            self.after_cancel(self._job)
        self._running = False
        self._time_left = MODES[self._mode]
        self._start_btn.configure(text="▶  Iniciar")
        self._redraw()

    def _set_mode(self, mode):
        self._mode = mode
        for key, btn in self._mode_btns.items():
            active = key == mode
            btn.configure(
                fg_color=C["red"] if active else C["neutral"],
                hover_color=C["red_hover"] if active else C["neutral_hov"],
            )
        self._reset()

    def _increase(self):
        self._time_left = min(self._time_left + 60, 99 * 60)
        self._redraw()

    def _decrease(self):
        self._time_left = max(self._time_left - 60, 60)
        self._redraw()


if __name__ == "__main__":
    app = PomodoroApp()
    app.mainloop()
