import cv2
import numpy as np
import pytest


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
