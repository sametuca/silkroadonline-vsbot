"""Read the minimap ("radar") in the top-right corner of the game window.

The radar ring has a fixed pixel size and is anchored to the window's top-right
corner. The player is the yellow arrow at its centre and every monster nearby
is a small bright-red square. Offsets are returned in radar pixels with the
y axis pointing UP (mathematical orientation), relative to the player.
"""

import cv2
import numpy as np

CENTER_FROM_RIGHT = 64   # px from the client area's right edge to the ring centre
CENTER_FROM_TOP = 108    # px from the client area's top edge to the ring centre
RADIUS = 48              # usable radius of the map disc, px
MIN_DOT_AREA, MAX_DOT_AREA = 3, 45


def geometry(shape):
    """(cx, cy, radius) of the radar disc in client pixels."""
    return shape[1] - CENTER_FROM_RIGHT, CENTER_FROM_TOP, RADIUS


def read_dots(frame):
    """Red monster dots as [(dx, dy_up)] relative to the player, in radar pixels."""
    cx, cy, r = geometry(frame.shape)
    h, w = frame.shape[:2]
    x0, y0 = max(0, cx - r - 2), max(0, cy - r - 2)
    x1, y1 = min(w, cx + r + 3), min(h, cy + r + 3)
    if x1 - x0 < 10 or y1 - y0 < 10:
        return []
    hsv = cv2.cvtColor(frame[y0:y1, x0:x1], cv2.COLOR_BGR2HSV)
    hue, sat, val = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
    mask = (((hue <= 8) | (hue >= 172)) & (sat > 190) & (val > 190)).astype(np.uint8)
    count, _, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)

    dots = []
    for i in range(1, count):
        area = stats[i, cv2.CC_STAT_AREA]
        bw, bh = stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT]
        if not (MIN_DOT_AREA <= area <= MAX_DOT_AREA) or max(bw, bh) > 9:
            continue
        dx, dy = centroids[i][0] + x0 - cx, centroids[i][1] + y0 - cy
        if dx * dx + dy * dy <= r * r:
            dots.append((float(dx), float(-dy)))
    return _merge_close(dots)


def _merge_close(dots, gap=5.0):
    """A dot's dark outline can split it into two blobs: fuse blobs closer than `gap` px."""
    merged = []
    for x, y in dots:
        for i, (mx, my, n) in enumerate(merged):
            if (x - mx) ** 2 + (y - my) ** 2 <= gap * gap:
                merged[i] = ((mx * n + x) / (n + 1), (my * n + y) / (n + 1), n + 1)
                break
        else:
            merged.append((x, y, 1))
    return [(x, y) for x, y, _ in merged]
