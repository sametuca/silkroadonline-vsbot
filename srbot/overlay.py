"""Draw boxes over the monsters the bot found, directly on top of the game window.

The overlay is a borderless, transparent, click-through window laid over the
game's client area: mouse clicks (including the bot's own) pass straight
through it, and it never takes focus. Only saturated colours are used (green,
red, blue, never white), so the bot's own screen reading, which looks for
white text and red radar dots, is not disturbed.
"""

import time
import tkinter as tk
from dataclasses import dataclass

from . import winutil
from .recorder import sprite_box

KEY = "#010203"            # colour that is see-through
GREEN, RED, BLUE = "#2bff2b", "#ff3030", "#3fa0ff"
LABEL_MARGIN = 6           # px kept between a box and the name label, so OCR crops stay clean
RADAR_SIZE = (170, 200)    # top-right corner the radar occupies: never draw there
STALE_AFTER = 1.5          # seconds after which boxes from an old scan are dropped


@dataclass
class Shape:
    kind: str       # "rect" | "circle" | "tag"
    x: int
    y: int
    w: int = 0
    h: int = 0
    color: str = GREEN
    text: str = ""


def _union(a, b):
    x0, y0 = min(a[0], b[0]), min(a[1], b[1])
    x1, y1 = max(a[0] + a[2], b[0] + b[2]), max(a[1] + a[3], b[1] + b[3])
    return x0, y0, x1 - x0, y1 - y0


def build_shapes(dets, shape, target=None, roam_point=None):
    """Turn detections into drawing primitives, in client pixels.

    target: click position (x, y) of the monster being attacked, drawn in red.
    roam_point: where the bot is walking to, drawn as a blue circle.
    """
    h, w = shape[:2]
    shapes = []
    for d in dets:
        lx, ly, lw, lh = d.box
        if d.source == "ocr":
            box = _union((lx - LABEL_MARGIN, ly - LABEL_MARGIN, lw + 2 * LABEL_MARGIN, lh + 2 * LABEL_MARGIN),
                         sprite_box(d, shape))
        else:
            box = d.box
        x, y, bw, bh = box
        is_target = target is not None and abs(d.click[0] - target[0]) < 45 and abs(d.click[1] - target[1]) < 45
        shapes.append(Shape("rect", x, y, bw, bh, RED if is_target else GREEN))
        if is_target:
            shapes.append(Shape("tag", x, max(0, y - 16), color=RED, text="HEDEF"))
            shapes.append(Shape("circle", d.click[0], d.click[1], 7, 7, RED))
    if roam_point is not None:
        shapes.append(Shape("circle", int(roam_point[0]), int(roam_point[1]), 10, 10, BLUE))
    # nothing may be drawn on the radar: the bot reads its red dots
    rx0 = w - RADAR_SIZE[0]
    return [s for s in shapes if not (s.x + s.w > rx0 and s.y < RADAR_SIZE[1])]


class Overlay:
    def __init__(self, root):
        self.root = root
        self.top = None
        self.canvas = None
        self._geometry = None

    def _create(self):
        top = tk.Toplevel(self.root)
        top.overrideredirect(True)
        top.attributes("-topmost", True)
        top.attributes("-transparentcolor", KEY)
        top.configure(bg=KEY)
        canvas = tk.Canvas(top, bg=KEY, highlightthickness=0, bd=0)
        canvas.pack(fill="both", expand=True)
        top.update_idletasks()
        winutil.make_click_through(top.winfo_id())
        self.top, self.canvas = top, canvas

    def draw(self, rect, shapes):
        """Show the overlay over the client rect (left, top, right, bottom) with these shapes."""
        if self.top is None:
            self._create()
        left, top, right, bottom = rect
        geometry = f"{right - left}x{bottom - top}+{left}+{top}"
        if geometry != self._geometry:
            self.top.geometry(geometry)
            self._geometry = geometry
        self.top.deiconify()
        self.canvas.delete("all")
        for s in shapes:
            if s.kind == "rect":
                self.canvas.create_rectangle(s.x, s.y, s.x + s.w, s.y + s.h, outline=s.color, width=2)
            elif s.kind == "circle":
                self.canvas.create_oval(s.x - s.w, s.y - s.h, s.x + s.w, s.y + s.h, outline=s.color, width=2)
            elif s.kind == "tag":
                self.canvas.create_text(s.x + 2, s.y, text=s.text, fill=s.color, anchor="sw",
                                        font=("Segoe UI", 9, "bold"))
        # Re-assert the stacking order: a game that was just focused can otherwise cover the overlay.
        self.top.attributes("-topmost", True)

    def hide(self):
        if self.top is not None and self.top.state() != "withdrawn":
            self.top.withdraw()

    def close(self):
        if self.top is not None:
            self.top.destroy()
            self.top = self.canvas = None


class OverlayState:
    """What the GUI feeds the overlay: the latest scan plus short-lived markers."""

    def __init__(self):
        self.scan = None          # (time, frame_shape, detections)
        self.roam = None          # (time, (x, y))
        self.flash_until = 0.0    # show regardless of focus until then (used by the test scan)

    def update_scan(self, shape, dets):
        self.scan = (time.time(), shape, list(dets))

    def update_roam(self, point):
        self.roam = (time.time(), point)

    def flash(self, seconds=3.0):
        self.flash_until = time.time() + seconds

    def shapes(self, target=None, now=None):
        now = now if now is not None else time.time()
        if not self.scan or now - self.scan[0] > STALE_AFTER and now > self.flash_until:
            return []
        _, shape, dets = self.scan
        roam = self.roam[1] if self.roam and now - self.roam[0] < 1.5 else None
        return build_shapes(dets, shape, target, roam)
