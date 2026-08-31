"""One-shot reference matching via ORB keypoints/descriptors.

This is deliberately not a "trained model" in the deep-learning sense -
training something that actually generalizes needs hundreds of labeled
examples, a GPU, and a much bigger runtime dependency, none of which fits
"add 1-2 crops and go." ORB (built into OpenCV, already a dependency - no
download, no training step) is the classical-CV answer to the same
one-shot problem: it describes local gradient patterns around corners/
edges, so it survives lighting and color shifts that break pure HSV
matching, at the cost of needing a bit more visual structure in the crop
than a single flat color patch has.

This runs as an independent, parallel path alongside color detection in
bot_engine.py: if color finds nothing this cycle, this gets a shot at the
whole scene using a completely different signal (shape/texture, not hue).
"""

import cv2
import numpy as np

_MAX_SCAN_DIM = 640  # downscale the scene before ORB for speed; scores are scaled back up
_MIN_KEYPOINTS_TO_STORE = 4  # a near-blank crop yields too few features to ever match reliably


def _orb():
    # OpenCV's ORB defaults (edgeThreshold=31, patchSize=31) assume
    # normal-sized photos - on a small name-plate crop (often <40px tall)
    # that border margin excludes the *entire* image from candidacy and
    # ORB silently returns zero keypoints. Small values here are what
    # actually make this work on crops this size.
    return cv2.ORB_create(nfeatures=500, edgeThreshold=5, fastThreshold=5, patchSize=9)


class Reference:
    __slots__ = ("name", "keypoints", "descriptors", "w", "h")

    def __init__(self, name, gray):
        kp, des = _orb().detectAndCompute(gray, None)
        self.name = name
        self.keypoints = kp
        self.descriptors = des
        self.h, self.w = gray.shape[:2]

    @property
    def usable(self):
        return self.descriptors is not None and len(self.descriptors) >= _MIN_KEYPOINTS_TO_STORE


class ReferenceMatcher:
    """Holds every monster's reference crop(s) and scans a live scene for them."""

    def __init__(self):
        self.references = []  # list[Reference]
        self._matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)

    def add(self, name, bgr_crop) -> bool:
        """Returns False if the crop had too little visual structure to be usable
        (e.g. a near-solid-color box) - caller should tell the user to pick a
        crop with more of the glyph shapes visible."""
        gray = cv2.cvtColor(bgr_crop, cv2.COLOR_BGR2GRAY)
        ref = Reference(name, gray)
        if not ref.usable:
            return False
        self.references.append(ref)
        return True

    def remove(self, name):
        self.references = [r for r in self.references if r.name != name]

    def clear(self):
        self.references.clear()

    def has_data(self):
        return len(self.references) > 0

    def find_in_scene(self, scene_bgr, target_names=None, min_good_matches=8, ratio=0.75):
        """Scan the whole scene for any stored reference.

        Returns (name, center_x, center_y, w, h) in scene_bgr's own pixel
        coordinates, or None. Independent of color/HSV entirely - matches
        on ORB descriptors (local gradient patterns), so lighting/color
        drift that defeats HSV masking doesn't necessarily defeat this.
        """
        if not self.references:
            return None

        h, w = scene_bgr.shape[:2]
        scale = min(1.0, _MAX_SCAN_DIM / max(h, w)) if max(h, w) > 0 else 1.0
        scene_small = (cv2.resize(scene_bgr, (max(int(w * scale), 1), max(int(h * scale), 1)),
                                   interpolation=cv2.INTER_AREA) if scale < 1.0 else scene_bgr)

        gray = cv2.cvtColor(scene_small, cv2.COLOR_BGR2GRAY)
        kp2, des2 = _orb().detectAndCompute(gray, None)
        if des2 is None or len(kp2) < _MIN_KEYPOINTS_TO_STORE:
            return None

        best = None  # (score, name, cx, cy, w, h) in *scaled* coords
        for ref in self.references:
            if not ref.usable:
                continue
            if target_names and ref.name.lower() not in target_names:
                continue
            matches = self._matcher.knnMatch(ref.descriptors, des2, k=2)
            good = [m for pair in matches if len(pair) == 2
                    for m, n in [pair] if m.distance < ratio * n.distance]
            if len(good) < min_good_matches:
                continue
            pts = np.array([kp2[m.trainIdx].pt for m in good])
            cx, cy = pts.mean(axis=0)
            score = len(good)
            if best is None or score > best[0]:
                best = (score, ref.name, cx, cy, ref.w, ref.h)

        if best is None:
            return None
        _score, name, cx, cy, ref_w, ref_h = best
        return name, cx / scale, cy / scale, ref_w, ref_h
