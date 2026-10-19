"""YOLO inference on plain onnxruntime (no torch needed at run time)."""

import json
import os

import cv2
import numpy as np

from .paths import data_path

MODEL_DIR = data_path("models")
MODEL_FILE = os.path.join(MODEL_DIR, "monsters.onnx")
META_FILE = os.path.join(MODEL_DIR, "monsters.json")


def model_available():
    return os.path.isfile(MODEL_FILE) and os.path.isfile(META_FILE)


class YoloDetector:
    def __init__(self, model_path=None, meta_path=None):
        import onnxruntime as ort
        model_path, meta_path = model_path or MODEL_FILE, meta_path or META_FILE
        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)
        self.classes = meta["classes"]
        self.imgsz = int(meta.get("imgsz", 640))
        self.session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
        self.input_name = self.session.get_inputs()[0].name

    def _letterbox(self, bgr):
        h, w = bgr.shape[:2]
        r = min(self.imgsz / h, self.imgsz / w)
        nh, nw = int(round(h * r)), int(round(w * r))
        resized = cv2.resize(bgr, (nw, nh), interpolation=cv2.INTER_LINEAR)
        canvas = np.full((self.imgsz, self.imgsz, 3), 114, np.uint8)
        top, left = (self.imgsz - nh) // 2, (self.imgsz - nw) // 2
        canvas[top:top + nh, left:left + nw] = resized
        return canvas, r, left, top

    def predict(self, bgr, conf=0.4, iou=0.5):
        """Return [(class_name, confidence, (x, y, w, h))] in frame pixels."""
        canvas, r, left, top = self._letterbox(bgr)
        blob = canvas[:, :, ::-1].transpose(2, 0, 1)[None].astype(np.float32) / 255.0
        out = self.session.run(None, {self.input_name: np.ascontiguousarray(blob)})[0][0]
        out = out.T  # (N, 4 + nc)
        scores = out[:, 4:]
        cls = scores.argmax(1)
        confs = scores[np.arange(len(cls)), cls]
        keep = confs >= conf
        out, cls, confs = out[keep], cls[keep], confs[keep]
        if not len(out):
            return []
        boxes = np.stack([out[:, 0] - out[:, 2] / 2, out[:, 1] - out[:, 3] / 2, out[:, 2], out[:, 3]], 1)
        idx = cv2.dnn.NMSBoxes(boxes.tolist(), confs.tolist(), conf, iou)
        fh, fw = bgr.shape[:2]
        results = []
        for i in np.array(idx).reshape(-1):
            x, y, w, h = boxes[i]
            x, y = (x - left) / r, (y - top) / r
            w, h = w / r, h / r
            x0, y0 = max(0, int(x)), max(0, int(y))
            x1, y1 = min(fw, int(x + w)), min(fh, int(y + h))
            if x1 > x0 and y1 > y0:
                results.append((self.classes[int(cls[i])], float(confs[i]), (x0, y0, x1 - x0, y1 - y0)))
        return results
