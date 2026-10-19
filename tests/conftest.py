from pathlib import Path

import cv2
import numpy as np
import pytest

FIXTURES = Path(__file__).parent / "fixtures"


def make_scene(labels, size=(632, 802)):
    """Game-like frame: noisy green ground with white, dark-outlined name labels.

    labels: [(text, x, y)] with (x, y) the text baseline start.
    """
    h, w = size
    rng = np.random.default_rng(0)
    img = np.zeros((h, w, 3), np.uint8)
    img[:] = (40, 110, 50)
    img = np.clip(img + rng.integers(-12, 12, img.shape), 0, 255).astype(np.uint8)
    for text, x, y in labels:
        cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    return img


@pytest.fixture
def scene():
    return make_scene


def add_radar(img):
    """Paste a real radar capture (5 red dots) into the top-right corner, where the game draws it."""
    # np.fromfile + imdecode: cv2.imread cannot open paths with non-ASCII characters on Windows
    radar = cv2.imdecode(np.fromfile(FIXTURES / "radar_live.png", np.uint8), cv2.IMREAD_COLOR)
    out = img.copy()
    out[0:radar.shape[0], out.shape[1] - radar.shape[1]:] = radar
    return out
