"""Color-based candidate detection and HP-bar reading.

Rationale: scanning an entire viewport with template matching every frame
is slow and fragile (lighting/zoom/rotation all break a raw pixel match).
Monster name-plates in Silkroad are rendered in a small set of flat,
saturated colors that are very stable under an HSV mask regardless of what
the 3D scene behind them looks like. So the pipeline here is:

  1. HSV color mask -> connected components -> a short list of candidate
     boxes (cheap, resolution-independent, ~milliseconds).
  2. (optional, see detection.py) refine each candidate with template/edge
     matching or OCR - only on those small crops, not the whole screen.

The HP-bar reader uses the same idea: a health bar is just a rectangle of
flat color whose filled width encodes a percentage - no ML needed to read
it precisely.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple

import cv2
import numpy as np

HSVRange = Tuple[Tuple[int, int, int], Tuple[int, int, int]]

# Reasonable starting point for a hostile-monster nameplate: warm
# orange/red text. Servers/UI skins vary, so this is meant to be
# recalibrated per-server with `sample_hsv_at`.
DEFAULT_NAMEPLATE_HSV: HSVRange = ((0, 120, 140), (20, 255, 255))


@dataclass
class Candidate:
    x: int
    y: int
    w: int
    h: int

    @property
    def center(self):
        return self.x + self.w // 2, self.y + self.h // 2


def sample_hsv_at(bgr_image, x, y, tolerance=(10, 60, 60)):
    """Sample the color at (x, y) and return an HSV range around it.

    Used by the GUI's "calibrate nameplate color" eyedropper: click once on
    a monster's name in a live screenshot and derive a mask range from it,
    instead of guessing HSV numbers by hand.
    """
    hsv = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2HSV)
    h, s, v = [int(c) for c in hsv[y, x]]
    th, ts, tv = tolerance
    lower = (max(h - th, 0), max(s - ts, 0), max(v - tv, 0))
    upper = (min(h + th, 179), min(s + ts, 255), min(v + tv, 255))
    return lower, upper


def find_candidates(bgr_image, hsv_range: HSVRange = DEFAULT_NAMEPLATE_HSV,
                     min_area=15, max_area=6000, max_results=12) -> List[Candidate]:
    """Return connected-component bounding boxes matching an HSV range."""
    hsv = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2HSV)
    lower, upper = hsv_range
    mask = cv2.inRange(hsv, np.array(lower, dtype=np.uint8), np.array(upper, dtype=np.uint8))

    # close small gaps between glyph strokes so a name reads as one blob
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    candidates = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area or area > max_area:
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        candidates.append(Candidate(x, y, w, h))

    # largest first - a stronger color match is usually a cleaner name-plate
    candidates.sort(key=lambda c: c.w * c.h, reverse=True)
    return candidates[:max_results]


def read_hp_ratio(bgr_image, rect, filled_hsv_range: HSVRange, empty_hsv_range: Optional[HSVRange] = None):
    """Read a health bar's fill ratio (0.0-1.0) from a fixed-position crop.

    rect = (x, y, w, h) within `bgr_image`. Counts filled-color pixels
    across the bar's width; far more reliable than a detection timeout for
    knowing a target actually died.
    """
    x, y, w, h = rect
    if w <= 0 or h <= 0:
        return None
    crop = bgr_image[y:y + h, x:x + w]
    if crop.size == 0:
        return None

    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    lower, upper = filled_hsv_range
    filled_mask = cv2.inRange(hsv, np.array(lower, dtype=np.uint8), np.array(upper, dtype=np.uint8))

    # count filled columns (any filled pixel in that column) rather than raw
    # pixel count, so a partially-occluded bar doesn't skew the ratio
    col_has_fill = filled_mask.any(axis=0)
    ratio = float(col_has_fill.sum()) / float(w)

    if empty_hsv_range is not None:
        empty_mask = cv2.inRange(hsv, np.array(empty_hsv_range[0], dtype=np.uint8),
                                  np.array(empty_hsv_range[1], dtype=np.uint8))
        total_bar = filled_mask | empty_mask
        col_is_bar = total_bar.any(axis=0)
        bar_width = max(int(col_is_bar.sum()), 1)
        ratio = float(col_has_fill.sum()) / float(bar_width)

    return max(0.0, min(1.0, ratio))
