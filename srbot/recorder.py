"""Records training data for the YOLO detector (phase C) while you play or hunt.

Every saved frame is auto-labelled: the OCR-matched name label tells us
*what* the monster is, and the sprite is always drawn right below its label,
so a box can be derived from the label geometry. No hand drawing needed.

Dataset layout (YOLO format, ready for training):
    dataset/images/<stamp>.jpg
    dataset/labels/<stamp>.txt     -> "class cx cy w h", normalised
    dataset/classes.txt            -> one monster name per line (line = class id)
"""

import os
import threading
import time

import cv2
import numpy as np

from . import detect, winutil
from .capture import ScreenGrabber
from .paths import data_path

SPRITE_W = 0.5     # sprite width  / label width   (measured on Destiny Online)
SPRITE_H = 2.8     # sprite height / label height
SPRITE_GAP = -2    # px between label bottom and sprite top
MIN_INTERVAL = 1.0  # seconds between saved frames
MIN_CHANGE = 4.0    # mean grey difference vs. last saved frame (skip near-duplicates)


def sprite_box(det, shape):
    """Estimate the monster sprite box (x, y, w, h) from its name label."""
    x, y, w, h = det.box
    sw, sh = max(12, int(w * SPRITE_W)), int(h * SPRITE_H)
    sx = x + w // 2 - sw // 2
    sy = y + h + SPRITE_GAP
    fh, fw = shape[:2]
    x0, y0 = max(0, sx), max(0, sy)
    x1, y1 = min(fw, sx + sw), min(fh, sy + sh)
    return x0, y0, x1 - x0, y1 - y0


class Dataset:
    def __init__(self, root=None):
        self.root = root or data_path("dataset")
        self.images = os.path.join(self.root, "images")
        self.labels = os.path.join(self.root, "labels")
        self.classes_file = os.path.join(self.root, "classes.txt")
        self.classes = self._load_classes()

    def _load_classes(self):
        try:
            with open(self.classes_file, encoding="utf-8") as f:
                return [line.strip() for line in f if line.strip()]
        except OSError:
            return []

    def class_id(self, name):
        if name not in self.classes:
            self.classes.append(name)
            os.makedirs(self.root, exist_ok=True)
            with open(self.classes_file, "w", encoding="utf-8") as f:
                f.write("\n".join(self.classes) + "\n")
        return self.classes.index(name)

    def count(self):
        if not os.path.isdir(self.images):
            return 0
        return len([f for f in os.listdir(self.images) if f.endswith(".jpg")])

    def save(self, frame, dets):
        """Write one image + label file. Returns the number of boxes saved."""
        fh, fw = frame.shape[:2]
        lines = []
        for d in dets:
            if not d.name or d.source != "ocr":
                continue
            x, y, w, h = sprite_box(d, frame.shape)
            if w < 8 or h < 8:
                continue
            lines.append(f"{self.class_id(d.name)} {(x + w / 2) / fw:.6f} {(y + h / 2) / fh:.6f} "
                         f"{w / fw:.6f} {h / fh:.6f}")
        if not lines:
            return 0
        os.makedirs(self.images, exist_ok=True)
        os.makedirs(self.labels, exist_ok=True)
        stamp = time.strftime("%Y%m%d_%H%M%S") + f"_{int(time.time() * 1000) % 1000:03d}"
        cv2.imwrite(os.path.join(self.images, stamp + ".jpg"), frame, [cv2.IMWRITE_JPEG_QUALITY, 92])
        with open(os.path.join(self.labels, stamp + ".txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        return len(lines)


class Recorder:
    """Throttled, de-duplicating front for Dataset. Thread-safe enough: one writer at a time."""

    def __init__(self, dataset=None):
        self.dataset = dataset or Dataset()
        self.enabled = False
        self.saved = self.dataset.count()
        self._last_time = 0.0
        self._last_small = None
        self._lock = threading.Lock()

    def maybe_save(self, frame, dets):
        # Only OCR detections carry label geometry we can derive sprite boxes from.
        if not self.enabled or not any(d.name and d.source == "ocr" for d in dets):
            return False
        now = time.time()
        with self._lock:
            if now - self._last_time < MIN_INTERVAL:
                return False
            small = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (64, 48)).astype(np.float32)
            if self._last_small is not None and float(np.abs(small - self._last_small).mean()) < MIN_CHANGE:
                return False
            if self.dataset.save(frame, dets):
                self._last_time, self._last_small = now, small
                self.saved += 1
                return True
        return False


class RecorderThread(threading.Thread):
    """Records while you play manually - no keys or clicks are ever sent."""

    def __init__(self, cfg, hwnd, recorder, on_log=None, on_frame=None):
        super().__init__(daemon=True)
        self.cfg, self.hwnd, self.recorder = cfg, hwnd, recorder
        self.on_log = on_log or (lambda m: None)
        self.on_frame = on_frame or (lambda f, d: None)
        self._stop_evt = threading.Event()

    def stop(self):
        self._stop_evt.set()

    def run(self):
        grabber = ScreenGrabber()
        self.on_log("Kayıt başladı. Normal oyna; bot tuş göndermiyor.")
        try:
            while not self._stop_evt.is_set() and self.recorder.enabled:
                rect = winutil.get_window_client_rect_on_screen(self.hwnd)
                frame = grabber.grab_bgr(rect) if rect else None
                if frame is not None:
                    dets = detect.detect(frame, self.cfg, mode="ocr")
                    self.on_frame(frame, dets)
                    self.recorder.maybe_save(frame, dets)
                self._stop_evt.wait(self.cfg.scan_interval)
        finally:
            grabber.close()
            self.on_log(f"Kayıt durdu. Veri setinde {self.recorder.saved} kare var.")
