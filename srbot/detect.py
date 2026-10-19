"""Find monster name labels on screen.

Name labels are small, bright, low-saturation text with a dark outline. We
find text-like blobs with plain image processing, read each blob with a
recognition-only OCR pass (fast, no text-detection model) and fuzzy-match
the result against the user's monster list. No templates, no colour
calibration.
"""

import os
from dataclasses import dataclass

import cv2
import numpy as np
from rapidfuzz import fuzz

REF_HEIGHT = 632.0  # layout constants below are tuned for this window height

_ocr = None


def _get_ocr():
    global _ocr
    if _ocr is None:
        from rapidocr_onnxruntime import RapidOCR
        _ocr = RapidOCR()
    return _ocr


@dataclass
class Detection:
    text: str
    name: str          # matched monster name from the list ("" in learn mode)
    score: float       # OCR confidence * fuzzy ratio, 0-1
    box: tuple         # x, y, w, h in client pixels (label box for OCR, sprite box for model)
    click: tuple       # where to click to select the monster
    source: str = "ocr"  # "ocr" | "model"


def _excluded_mask(shape, excludes):
    h, w = shape[:2]
    mask = np.zeros((h, w), np.uint8)
    for l, t, r, b in excludes:
        mask[int(t * h):int(b * h), int(l * w):int(r * w)] = 255
    return mask


def find_label_boxes(bgr, excludes):
    """Return (x, y, w, h) boxes of white-ish text blobs outside excluded areas."""
    h, w = bgr.shape[:2]
    s = h / REF_HEIGHT
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    mask = ((hsv[:, :, 1] < 70) & (hsv[:, :, 2] > 205)).astype(np.uint8) * 255
    mask[_excluded_mask(bgr.shape, excludes) > 0] = 0

    kw = max(5, int(round(7 * s)))
    blobs = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_RECT, (kw, 3)))
    contours, _ = cv2.findContours(blobs, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes = []
    for c in contours:
        x, y, bw, bh = cv2.boundingRect(c)
        if not (6 * s <= bh <= 22 * s and 22 * s <= bw <= 220 * s):
            continue
        fill = cv2.countNonZero(mask[y:y + bh, x:x + bw]) / float(bw * bh)
        if not 0.10 <= fill <= 0.75:
            continue
        boxes.append((x, y, bw, bh))
    return boxes


def _read(bgr, box):
    x, y, bw, bh = box
    pad = 3
    h, w = bgr.shape[:2]
    crop = bgr[max(0, y - pad):min(h, y + bh + pad), max(0, x - pad):min(w, x + bw + pad)]
    if crop.size == 0:
        return "", 0.0
    crop = cv2.resize(crop, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    try:
        result, _ = _get_ocr()(crop, use_det=False, use_cls=False, use_rec=True)
    except Exception:
        return "", 0.0
    if not result:
        return "", 0.0
    return result[0][0].strip(), float(result[0][1])


def _norm(text):
    return "".join(ch for ch in text.lower() if ch.isalnum() or ch == " ").strip()


_yolo = None
_yolo_mtime = None


def _get_yolo():
    """Load the trained model lazily; reload when the file changes (after training)."""
    global _yolo, _yolo_mtime
    from . import yolo
    if not yolo.model_available():
        return None
    mtime = os.path.getmtime(yolo.MODEL_FILE)
    if _yolo is None or mtime != _yolo_mtime:
        try:
            _yolo, _yolo_mtime = yolo.YoloDetector(), mtime
        except Exception:
            _yolo, _yolo_mtime = None, mtime
    return _yolo


def active_mode(cfg):
    """Which detector will really run for this config: "model" or "ocr"."""
    if cfg.detector != "ocr" and _get_yolo() is not None:
        return "model"
    return "ocr"


def detect_model(bgr, cfg, model):
    wanted = {m.lower(): m for m in cfg.monsters if m.strip()}
    results = []
    for cls_name, conf, box in model.predict(bgr, conf=cfg.model_conf):
        name = wanted.get(cls_name.lower())
        if not name:
            continue
        x, y, w, h = box
        # click a bit above the box centre: the body, not the feet
        results.append(Detection(cls_name, name, conf, box, (x + w // 2, y + int(h * 0.45)), "model"))
    return results


def detect(bgr, cfg, learn=False, mode=None):
    """Detect monsters. mode: None = per cfg.detector, or force "ocr".
    In learn mode every readable label is returned (always OCR)."""
    if not learn and mode != "ocr" and active_mode(cfg) == "model":
        return detect_model(bgr, cfg, _get_yolo())
    return detect_ocr(bgr, cfg, learn)


def detect_ocr(bgr, cfg, learn=False):
    """OCR path: name labels -> fuzzy match against the monster list."""
    s = bgr.shape[0] / REF_HEIGHT
    known = [(m, _norm(m)) for m in cfg.monsters if m.strip()]
    results = []
    for box in find_label_boxes(bgr, cfg.excludes):
        text, conf = _read(bgr, box)
        norm = _norm(text)
        if len(norm) < 3 or conf < 0.5:
            continue
        name, ratio = "", 0.0
        for original, n in known:
            r = fuzz.ratio(norm, n)
            if r > ratio:
                name, ratio = original, r
        if not learn and ratio < cfg.match_threshold:
            continue
        if learn and cfg.player_name and fuzz.ratio(norm, _norm(cfg.player_name)) > 85:
            continue
        x, y, bw, bh = box
        click = (x + bw // 2, int(y + bh + cfg.click_offset * s))
        results.append(Detection(text, name if ratio >= cfg.match_threshold else "",
                                 conf * ratio / 100.0 if known else conf, box, click))
    return results


@dataclass
class TargetGroup:
    name: str     # most common reading of this name
    count: int    # how many such labels are on screen at once
    boxes: list   # label boxes (client pixels) from the frame that showed the most


def _looks_like_name(text):
    letters = sum(ch.isalpha() for ch in text)
    return 3 <= len(text) <= 24 and letters >= 0.85 * len(text.replace(" ", ""))


def find_targets(frames, cfg, player_name=""):
    """Group the readable name labels on screen into candidate monster names.

    `frames` is one or more screenshots of the same moment (a label missed by
    OCR in one is usually caught in another). Labels with the same name -
    normal, champion and giant monsters all share it - end up in one group.
    The player's own name is dropped. Largest group first.
    """
    own = _norm(player_name)
    groups = []  # each: {"names": Counter-like dict, "norm": str, "count": int, "boxes": list}
    for frame in frames:
        per_frame = []
        for d in detect_ocr(frame, cfg, learn=True):
            text = " ".join(d.text.split())
            norm = _norm(text)
            if not _looks_like_name(text) or (own and fuzz.ratio(norm, own) >= 80):
                continue
            slot = next((g for g in per_frame if fuzz.ratio(norm, g["norm"]) >= 85), None)
            if slot is None:
                slot = {"norm": norm, "names": {}, "count": 0, "boxes": []}
                per_frame.append(slot)
            slot["names"][text] = slot["names"].get(text, 0) + 1
            slot["count"] += 1
            slot["boxes"].append(d.box)
        for g in per_frame:  # merge into the running result, keeping the best count seen
            match = next((m for m in groups if fuzz.ratio(g["norm"], m["norm"]) >= 85), None)
            if match is None:
                groups.append(g)
                continue
            for text, n in g["names"].items():
                match["names"][text] = match["names"].get(text, 0) + n
            if g["count"] > match["count"]:
                match["count"], match["boxes"] = g["count"], g["boxes"]
    groups.sort(key=lambda g: -g["count"])
    return [TargetGroup(max(g["names"], key=g["names"].get), g["count"], g["boxes"]) for g in groups]
