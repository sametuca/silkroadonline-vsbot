"""Walk around to find monsters when none are on screen.

Silkroad-style games move the character to wherever you click on the
ground, so roaming is just "click a ground point a bit away from the
player". The walk keeps a heading for a few steps (so it explores instead
of jittering in place) and then turns. Points never land on the UI.
"""

import math
import random

from .detect import REF_HEIGHT

# Where the ground is, as fractions of the game window: above the chat and skill bar,
# clear of the minimap on the right.
GROUND = (0.12, 0.22, 0.80, 0.64)
PLAYER = (0.50, 0.55)          # the character stands near here
PERSPECTIVE = 0.6              # vertical distances look shorter than horizontal ones
STEPS_PER_HEADING = 4


class Roamer:
    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.heading = self.rng.uniform(0, 2 * math.pi)
        self.steps_left = STEPS_PER_HEADING

    def next_point(self, shape, step_px, excludes=()):
        """Pick a screen point (x, y) in client pixels to walk to."""
        h, w = shape[:2]
        step = step_px * h / REF_HEIGHT
        px, py = w * PLAYER[0], h * PLAYER[1]
        x0, y0, x1, y1 = (GROUND[0] * w, GROUND[1] * h, GROUND[2] * w, GROUND[3] * h)

        for _ in range(12):
            if self.steps_left <= 0:
                self.heading += self.rng.choice((-1, 1)) * self.rng.uniform(math.pi / 3, math.pi * 0.85)
                self.steps_left = STEPS_PER_HEADING
            x = px + math.cos(self.heading) * step
            y = py + math.sin(self.heading) * step * PERSPECTIVE
            inside = x0 <= x <= x1 and y0 <= y <= y1
            on_ui = any(l * w <= x <= r * w and t * h <= y <= b * h for l, t, r, b in excludes)
            if inside and not on_ui:
                self.steps_left -= 1
                return int(x), int(y)
            self.steps_left = 0  # that way is blocked (edge of the ground area): turn

        return int(px), int(py + step * PERSPECTIVE)  # fallback: step toward the camera
