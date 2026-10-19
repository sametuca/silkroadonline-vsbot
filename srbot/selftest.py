"""Headless smoke test: `SilkroadVisionBot.exe --selftest result.txt`.

Verifies that everything the bot needs was really bundled (OCR models,
onnxruntime, OpenCV, GUI toolkit) by detecting a drawn name label. A
windowed exe has no console, so the verdict goes to a file and the exit code.
"""

import os
import traceback


def run(out_path):
    try:
        import customtkinter  # noqa: F401  (bundled GUI toolkit)
        import cv2
        import numpy as np
        import onnxruntime  # noqa: F401  (YOLO runtime)

        from .config import Config
        from .detect import detect
        from .paths import resource_path

        for asset in ("logo.png", "app_icon.png", "icon.ico"):  # bundled icons the GUI loads
            if not os.path.isfile(resource_path("assets", asset)):
                raise FileNotFoundError(f"missing bundled asset: {asset}")

        img = np.full((632, 802, 3), (40, 110, 50), np.uint8)
        cv2.putText(img, "Mangyang", (300, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(img, "Mangyang", (300, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        dets = detect(img, Config(monsters=["Mangyang"], excludes=[]), mode="ocr")
        ok = len(dets) == 1 and dets[0].name == "Mangyang"
        verdict = "OK" if ok else f"FAIL: unexpected detections {dets}"
    except Exception:
        ok, verdict = False, "FAIL:\n" + traceback.format_exc()
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(verdict + "\n")
    return 0 if ok else 1
