"""Fast screen capture.

Uses `mss` (low-level OS capture, no GDI round-trip) when available since it
is meaningfully faster than PIL.ImageGrab for a tight bot loop, and falls
back to PIL automatically so the app still runs if `mss` isn't installed.
Either way this only ever reads pixels already on screen.
"""

import numpy as np

try:
    import mss
except ImportError:
    mss = None

try:
    from PIL import ImageGrab
except ImportError:
    ImageGrab = None


class ScreenGrabber:
    """Not thread-safe by itself - create one instance per thread.

    mss keeps a handle to the capture backend open per-instance, which is
    why the bot loop's background thread owns its own ScreenGrabber rather
    than sharing one with the GUI thread.
    """

    def __init__(self):
        self._sct = mss.mss() if mss is not None else None

    def grab_bgr(self, bbox):
        """bbox = (left, top, right, bottom) absolute screen pixels.

        Returns an (H, W, 3) uint8 numpy array in BGR order (OpenCV's
        native order), or None if capture failed.
        """
        left, top, right, bottom = bbox
        width, height = right - left, bottom - top
        if width <= 0 or height <= 0:
            return None

        if self._sct is not None:
            try:
                shot = self._sct.grab({"left": left, "top": top, "width": width, "height": height})
                # mss gives BGRA - drop alpha, already BGR-ordered for cv2
                return np.array(shot)[:, :, :3]
            except Exception:
                pass  # fall through to PIL

        if ImageGrab is not None:
            try:
                pil_img = ImageGrab.grab(bbox=bbox)
                rgb = np.array(pil_img)
                return rgb[:, :, ::-1]  # RGB -> BGR
            except Exception:
                return None

        return None

    def close(self):
        if self._sct is not None:
            try:
                self._sct.close()
            except Exception:
                pass
