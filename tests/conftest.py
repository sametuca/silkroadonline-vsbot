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


def add_panel(img, fill):
    """Draw the game's target window (name strip + HP bar) at the top centre; fill is the HP fraction 0..1."""
    out = img.copy()
    cx = out.shape[1] // 2 - 2
    cv2.rectangle(out, (cx - 118, 8), (cx + 118, 84), (70, 70, 74), -1)             # window frame
    cv2.rectangle(out, (cx - 105, 11), (cx + 105, 31), (0, 0, 0), -1)               # black name strip
    cv2.rectangle(out, (cx - 102, 40), (cx + 106, 51), (48, 48, 52), -1)            # empty bar
    cv2.putText(out, "Lv 1   General   %d%%" % round(fill * 100), (cx - 100, 76), cv2.FONT_HERSHEY_SIMPLEX, 0.45,
                (235, 235, 235), 1, cv2.LINE_AA)                                  # info row text
    width = int(205 * fill)
    if width > 0:
        cv2.rectangle(out, (cx - 100, 42), (cx - 100 + width, 49), (30, 30, 210), -1)  # red fill (BGR)
    return out


def add_real_dead_panel(img):
    """Paste a real capture of the target window showing a corpse (empty bar, '0%')."""
    panel = cv2.imdecode(np.fromfile(FIXTURES / "target_dead.png", np.uint8), cv2.IMREAD_COLOR)
    out = img.copy()
    out[0:panel.shape[0], 250:250 + panel.shape[1]] = panel
    return out


@pytest.fixture(autouse=True)
def isolated_debug_dir(monkeypatch, tmp_path):
    """Tests must never leave diagnostic frames (debug/) in the project folder."""
    from srbot import engine
    monkeypatch.setattr(engine, "data_path", lambda *parts: str(tmp_path.joinpath(*parts)))
