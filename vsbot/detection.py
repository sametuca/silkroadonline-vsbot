"""Monster detection: a layered pipeline instead of one flat technique.

Layers, cheapest/most-robust first:

  1. Color candidates (color_detect.find_candidates) - fast, survives
     zoom/lighting changes because it only cares about the nameplate's
     hue, not its exact pixels.
  2. Multi-scale edge template matching, run only on the small crops
     around each candidate (not the whole screen) - confirms *which*
     monster it is and gives a precise click point. Edges (Canny) instead
     of raw grayscale so a slightly different zoom level still matches.
  3. Optional OCR + fuzzy text match (vsbot.ocr) as a swap-in for step 2
     when the caller wants to match by the monster's actual printed name
     rather than a pixel template.

A plain "color only" mode is also exposed for people who don't want to
prepare template PNGs at all.
"""

import os
import time
from dataclasses import dataclass
from typing import List, Optional

import cv2
import numpy as np

from . import color_detect, ocr


def _imread_unicode(path, flags=cv2.IMREAD_COLOR):
    """cv2.imread silently returns None for paths with non-ASCII characters
    on Windows (it doesn't go through a wide-character/UTF-8 file open) -
    and this project's own folder name ("Masaüstü") is exactly such a path.
    Reading the bytes via Python's own (Unicode-safe) file I/O and decoding
    with cv2.imdecode sidesteps that entirely."""
    try:
        data = np.fromfile(path, dtype=np.uint8)
    except OSError:
        return None
    if data.size == 0:
        return None
    return cv2.imdecode(data, flags)


class MonsterTemplate:
    __slots__ = ("name", "path", "gray", "w", "h")

    def __init__(self, name, path, gray):
        self.name = name
        self.path = path
        self.gray = gray
        self.h, self.w = gray.shape[:2]


def sanitize_template_basename(name):
    keep = "-_"
    cleaned = "".join(c for c in name.strip() if c.isalnum() or c in keep)
    return cleaned.lower() or "template"


def load_monster_templates(folder) -> List[MonsterTemplate]:
    templates = []
    if not os.path.isdir(folder):
        return templates
    for fname in sorted(os.listdir(folder)):
        if not fname.lower().endswith(".png"):
            continue
        path = os.path.join(folder, fname)
        img = _imread_unicode(path, cv2.IMREAD_COLOR)
        if img is None:
            continue
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        templates.append(MonsterTemplate(os.path.splitext(fname)[0], path, gray))
    return templates


@dataclass
class Detection:
    template_name: str
    confidence: float
    left: int
    top: int
    w: int
    h: int

    @property
    def center_x(self):
        return self.left + self.w // 2

    @property
    def center_y(self):
        return self.top + self.h // 2


_SCALES = (0.85, 0.92, 1.0, 1.08, 1.15)


def _edges(gray):
    return cv2.Canny(gray, 60, 160)


def _best_multiscale_match(region_gray, tpl_gray, scales=_SCALES):
    """Slide `tpl_gray` (at a few scales) over `region_gray` using edges.

    Returns (score, x, y, w, h) in region_gray's coordinate space, or None.
    """
    if region_gray.size == 0:
        return None
    region_edges = _edges(region_gray)
    if not region_edges.any():
        return None

    best = None
    for scale in scales:
        w = max(int(round(tpl_gray.shape[1] * scale)), 1)
        h = max(int(round(tpl_gray.shape[0] * scale)), 1)
        if w >= region_gray.shape[1] or h >= region_gray.shape[0] or w < 6 or h < 6:
            continue
        interp = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR
        resized = cv2.resize(tpl_gray, (w, h), interpolation=interp)
        tpl_edges = _edges(resized)
        if not tpl_edges.any():
            continue
        result = cv2.matchTemplate(region_edges, tpl_edges, cv2.TM_CCOEFF_NORMED)
        _min_val, max_val, _min_loc, max_loc = cv2.minMaxLoc(result)
        if best is None or max_val > best[0]:
            best = (max_val, max_loc[0], max_loc[1], w, h)
    return best


def base_monster_name(template_name):
    """Strip the "__vN" variant suffix (see gui.py's Add Monster step,
    which lets you stack multiple poses/angles of the same monster under
    one logical name - "wolf", "wolf__v2", "wolf__v3", ... all match as
    "wolf" for target filtering and in what gets reported/clicked)."""
    return template_name.split("__", 1)[0]


def detect_color_only(scene_bgr, hsv_range, target_names=None) -> Optional[Detection]:
    """No template needed at all - just the nearest color-matched blob."""
    h, w = scene_bgr.shape[:2]
    candidates = color_detect.find_candidates(scene_bgr, hsv_range, prefer_point=(w / 2, h / 2))
    if not candidates:
        return None
    best = candidates[0]  # nearest to scene center, i.e. nearest to the player
    return Detection("target", 1.0, best.x, best.y, best.w, best.h)


def detect_template(scene_bgr, templates, threshold, target_names=None) -> Optional[Detection]:
    """Full-frame multi-scale template search (no color pre-filter)."""
    if not templates:
        return None
    scene_gray = cv2.cvtColor(scene_bgr, cv2.COLOR_BGR2GRAY)
    best = None
    for tpl in templates:
        base = base_monster_name(tpl.name)
        if target_names and base.lower() not in target_names:
            continue
        match = _best_multiscale_match(scene_gray, tpl.gray)
        if match is None:
            continue
        score, x, y, w, h = match
        if score < threshold:
            continue
        if best is None or score > best.confidence:
            best = Detection(base, float(score), x, y, w, h)
    return best


def detect_hybrid(scene_bgr, templates, hsv_range, threshold, target_names=None, pad=14) -> Optional[Detection]:
    """Color candidates first, then template-confirm only those small crops.

    This is the recommended default: much faster than a full-frame
    template search (only a handful of small crops get matched, not the
    whole hunt region) and more tolerant of zoom drift than plain color
    detection (still tells monsters apart by shape, not just color).

    Among near-equal shape matches, the candidate closer to the scene
    center (roughly where the player stands) wins - mirrors how a player
    would naturally pick the nearest monster of the right kind rather
    than one further away, without letting proximity override a clearly
    stronger/weaker shape match.
    """
    if not templates:
        return detect_color_only(scene_bgr, hsv_range, target_names)

    scene_h, scene_w = scene_bgr.shape[:2]
    center = (scene_w / 2, scene_h / 2)
    max_dist = (scene_w ** 2 + scene_h ** 2) ** 0.5 or 1.0

    candidates = color_detect.find_candidates(scene_bgr, hsv_range, prefer_point=center)
    if not candidates:
        return None

    scene_gray = cv2.cvtColor(scene_bgr, cv2.COLOR_BGR2GRAY)

    best = None
    best_rank = -1.0
    for cand in candidates:
        x0 = max(cand.x - pad, 0)
        y0 = max(cand.y - pad, 0)
        x1 = min(cand.x + cand.w + pad, scene_w)
        y1 = min(cand.y + cand.h + pad, scene_h)
        crop = scene_gray[y0:y1, x0:x1]

        cx, cy = cand.x + cand.w / 2, cand.y + cand.h / 2
        dist_norm = ((cx - center[0]) ** 2 + (cy - center[1]) ** 2) ** 0.5 / max_dist

        for tpl in templates:
            base = base_monster_name(tpl.name)
            if target_names and base.lower() not in target_names:
                continue
            match = _best_multiscale_match(crop, tpl.gray)
            if match is None:
                continue
            score, mx, my, w, h = match
            if score < threshold:
                continue
            rank = score - 0.08 * dist_norm  # small nudge toward the nearer candidate
            if rank > best_rank:
                best_rank = rank
                best = Detection(base, float(score), x0 + mx, y0 + my, w, h)

    return best


def confirm_with_ocr(scene_bgr, found: Detection, target_names, reject_below=40, pad=6) -> bool:
    """Extra safety pass folded into the default (hybrid) pipeline: if
    Tesseract/easyocr happens to be installed, read the actual text on the
    winning candidate and check it roughly matches one of the names you're
    hunting. This runs OCR exactly once per cycle (only on the already-
    chosen candidate, not every candidate), so it doesn't change hybrid's
    speed profile even on the slower easyocr backend.

    Uses token_set_ratio rather than ocr.fuzzy_match's partial_ratio: real
    nameplates usually carry extra tokens ("Mangyang (Lv.1)", "Tiger Girl
    [INT] - (Level 20)") that partial_ratio isn't built to ignore, and it's
    lenient enough that an unrelated longer string can score deceptively
    high against a short target name - exactly wrong for a veto check.
    token_set_ratio scores a full match despite the extra tokens while
    still scoring genuinely different text low.

    Deliberately gives the benefit of the doubt on an empty read (small
    stylized game fonts aren't always legible to OCR) - it only vetoes a
    candidate whose text clearly contradicts every target name, which is
    the situation actually worth catching (a same-colored/shaped false
    positive - a UI icon, another player's name, etc).

    Returns True to keep the detection, False to discard it as a likely
    false positive. Always True if OCR isn't installed or there's nothing
    to compare against (no target_names set).
    """
    if not target_names or not ocr.is_available():
        return True

    scene_h, scene_w = scene_bgr.shape[:2]
    x0 = max(found.left - pad, 0)
    y0 = max(found.top - pad, 0)
    x1 = min(found.left + found.w + pad, scene_w)
    y1 = min(found.top + found.h + pad, scene_h)
    crop = scene_bgr[y0:y1, x0:x1]
    if crop.size == 0:
        return True

    text = ocr.read_text(crop)
    if not text:
        return True  # illegible crop - don't penalize for OCR's limits

    text_low = text.strip().lower()
    try:
        from rapidfuzz import fuzz
        best_score = max(fuzz.token_set_ratio(text_low, name.lower()) for name in target_names)
    except ImportError:
        import difflib
        best_score = max(difflib.SequenceMatcher(None, text_low, name.lower()).ratio() * 100
                          for name in target_names)
    return best_score >= reject_below


_OCR_MAX_CANDIDATES = 4  # bound the worst case: OCR is the slow part, don't spend it on every color blob


def detect_with_ocr(scene_bgr, hsv_range, target_names=None, min_score=70, pad=6) -> Optional[Detection]:
    """Color candidates, confirmed/named by reading the actual text (OCR).

    Two things keep this from calling OCR on every color blob in the hunt
    region (the actual reason a pure-OCR pass is slow - each call costs
    real milliseconds, and a full window can have a dozen color matches
    that aren't name-plates at all):

      1. Candidates come back nearest-to-center first (prefer_point) and
         filtered to a text-like aspect ratio (name-plates read as wider
         than tall; a near-square or tall blob is almost never text) -
         both cheap, OCR-free checks.
      2. Only the first `_OCR_MAX_CANDIDATES` survivors ever reach OCR.

    Returns None (rather than raising) if no OCR engine is installed -
    callers should check `vsbot.ocr.is_available()` before relying on this
    mode so the GUI can tell the user why nothing is happening.
    """
    if not ocr.is_available():
        return None

    scene_h, scene_w = scene_bgr.shape[:2]
    candidates = color_detect.find_candidates(scene_bgr, hsv_range, prefer_point=(scene_w / 2, scene_h / 2))
    text_like = [c for c in candidates if c.w >= c.h * 0.9][:_OCR_MAX_CANDIDATES]

    for cand in text_like:
        x0 = max(cand.x - pad, 0)
        y0 = max(cand.y - pad, 0)
        x1 = min(cand.x + cand.w + pad, scene_w)
        y1 = min(cand.y + cand.h + pad, scene_h)
        crop = scene_bgr[y0:y1, x0:x1]

        text = ocr.read_text(crop)
        if not text:
            continue

        if target_names:
            match, score = ocr.fuzzy_match(text, list(target_names), min_score=min_score)
            if match is None:
                continue
            name = match
        else:
            name = text.strip().lower().replace(" ", "_")[:32]
            score = 100

        return Detection(name, float(score) / 100.0, cand.x, cand.y, cand.w, cand.h)

    return None


class ReclickGuard:
    """Fallback "is this target already dead" signal for when no HP-bar
    region has been calibrated: remembers (name, approximate position)
    pairs for `lockout_seconds` and blocks re-clicking one.

    Prefer bot_engine's HP-bar death check when available - it's a
    measurement, this is a guess.
    """

    def __init__(self, lockout_seconds=2.5, position_tolerance=18):
        self.lockout_seconds = lockout_seconds
        self.position_tolerance = position_tolerance
        self._recent = []  # list of (name, x, y, timestamp)

    def set_lockout(self, seconds):
        self.lockout_seconds = max(0.0, float(seconds))

    def cleanup(self, now=None):
        now = now if now is not None else time.time()
        self._recent = [e for e in self._recent if now - e[3] < self.lockout_seconds]

    def is_recent(self, name, x, y, now=None):
        now = now if now is not None else time.time()
        self.cleanup(now)
        for (rname, rx, ry, _ts) in self._recent:
            if rname != name:
                continue
            if abs(rx - x) <= self.position_tolerance and abs(ry - y) <= self.position_tolerance:
                return True
        return False

    def remember(self, name, x, y, now=None):
        now = now if now is not None else time.time()
        self._recent.append((name, x, y, now))
