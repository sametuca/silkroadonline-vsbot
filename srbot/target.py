"""Read the game's target window (name + HP bar) to know whether the selected monster is alive.

Dead monsters lie on the ground and keep their name label, so "the label is gone"
never happens. The target window is the game's own, reliable signal: selecting
a corpse shows an EMPTY HP bar ("0%"), a live monster shows a filled bar.

The window sits at the top centre of the game window at a fixed pixel size
(about 235 x 75 px), so it is located relative to the window's horizontal centre.
"""

from dataclasses import dataclass

import cv2

PANEL_HALF_WIDTH = 118     # the window spans centre +/- this many px
PANEL_TOP, PANEL_BOTTOM = 6, 86
NAME_STRIP = (11, 31)      # y range of the black strip holding the monster's name
NAME_X = (-75, 85)         # x range (relative to the centre) of the name text
INFO_ROWS = (62, 80)       # y range of the "Lv / rarity / HP%" text row
BAR_ROWS = (42, 49)        # y range of the HP bar's fill, inside the bar frame
BAR_X = (-100, 104)        # x range (relative to the centre) of the bar's inside
DEAD_FILL = 0.04           # fill fraction at or below which the target counts as dead


@dataclass
class Panel:
    present: bool          # a target window is shown at all
    fill: float            # HP bar fill, 0..1 (0 when not present)
    name_box: tuple        # (x, y, w, h) of the name text in client pixels, for OCR
    dark: float = 0.0      # measurements behind the decision, for diagnostics
    contrast: float = 0.0
    text: int = 0

    @property
    def dead(self):
        return self.present and self.fill <= DEAD_FILL


def _centre(frame):
    return frame.shape[1] // 2 - 2


def read_panel(frame):
    """Locate and measure the target window. Pure image maths, a few milliseconds."""
    h, w = frame.shape[:2]
    cx = _centre(frame)
    x0, x1 = cx - PANEL_HALF_WIDTH, cx + PANEL_HALF_WIDTH
    if x0 < 0 or x1 > w or PANEL_BOTTOM > h:
        return Panel(False, 0.0, (0, 0, 0, 0))
    hsv = cv2.cvtColor(frame[0:PANEL_BOTTOM, x0:x1], cv2.COLOR_BGR2HSV)
    val, sat = hsv[:, :, 2], hsv[:, :, 1]

    # 1) the name strip is a solid dark band...
    ny0, ny1 = NAME_STRIP
    strip = val[ny0:ny1, 20:PANEL_HALF_WIDTH * 2 - 20]
    dark_fraction = float((strip < 60).mean())
    dark = dark_fraction > 0.6
    # ...framed by lighter metal (a dark map or a cave is dark everywhere, with no such contrast)...
    frame_above = float(val[5:10, 20:PANEL_HALF_WIDTH * 2 - 20].mean())
    contrast = frame_above - float(strip.mean())
    framed = contrast >= 25
    # ...and the info row under the bar carries bright text ("Lv 1  General  100%").
    text_pixels = int((val[INFO_ROWS[0]:INFO_ROWS[1], 10:PANEL_HALF_WIDTH * 2 - 10] > 170).sum())
    present = dark and framed and text_pixels >= 20
    metrics = {"dark": dark_fraction, "contrast": contrast, "text": text_pixels}
    name_box = (cx + NAME_X[0], ny0, NAME_X[1] - NAME_X[0], ny1 - ny0)
    if not present:
        return Panel(False, 0.0, name_box, **metrics)

    # 2) the fill is the saturated, bright colour inside the bar; an empty bar is dark grey
    by0, by1 = BAR_ROWS
    bx0, bx1 = cx + BAR_X[0] - x0, cx + BAR_X[1] - x0
    bar_sat, bar_val = sat[by0:by1, bx0:bx1], val[by0:by1, bx0:bx1]
    filled = (bar_sat > 110) & (bar_val > 110)
    fill = float(filled.any(axis=0).mean())  # fraction of bar columns that contain fill
    return Panel(True, fill, name_box, **metrics)
