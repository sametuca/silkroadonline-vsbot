"""Radar-guided roaming: look for monsters without leaving the farming area.

Silkroad-style games move the character to wherever you click on the ground.
Instead of walking at random, the bot

1. heads for the nearest red monster dot on the radar (they are monsters, so
   that is where the hunt continues),
2. never goes farther than `radius` from its home spot (where it was when the
   bot started): dots beyond the leash are ignored,
3. walks back home when the radar shows nothing, and only wanders in short
   steps around home.

Radar and screen directions may differ (the map can rotate with the camera or
stay north-up), so after every step the bot measures how the dots moved on the
radar and learns that rotation (`offset`) and the radar scale (`rho`).

All lengths here are "reference pixels" (a 632 px tall window) so the numbers
do not depend on the window size; callers scale with `scale`.
"""

import math
import random
from dataclasses import dataclass

from .detect import REF_HEIGHT

# Where the ground is, as fractions of the game window: above the chat and skill bar,
# clear of the minimap on the right.
GROUND = (0.12, 0.22, 0.80, 0.64)
PLAYER = (0.50, 0.55)          # the character stands near here
PERSPECTIVE = 0.6              # vertical distances look shorter than horizontal ones
RHO_START = 0.025              # radar px per ground px, refined from measurements
MATCH_RADIUS = 14.0            # px a dot may shift between two radar readings of the same monster
MIN_SHIFT = 2.0                # px of radar shift needed to trust a measurement


@dataclass
class Move:
    angle: float      # ground direction, radians, y up (screen-forward = pi/2)
    length: float     # reference px
    point: tuple      # where to click, client px
    reason: str       # "radar" | "home" | "wander"


def _circ_mean(a, b, weight):
    """Blend angle b into angle a with the given weight (0..1)."""
    x = (1 - weight) * math.cos(a) + weight * math.cos(b)
    y = (1 - weight) * math.sin(a) + weight * math.sin(b)
    return math.atan2(y, x)


class Roamer:
    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.offset = 0.0           # radar display angle = ground angle + offset
        self.rho = RHO_START
        self.pos = [0.0, 0.0]       # dead-reckoned position relative to home, reference px
        self.calibrated = False

    def reset_home(self):
        self.pos = [0.0, 0.0]

    @property
    def home_distance(self):
        return math.hypot(*self.pos)

    # -- planning --------------------------------------------------------
    def plan(self, dots, step, radius):
        """Choose (angle, length, reason) in reference px."""
        best = None
        for vx, vy in dots:
            angle = math.atan2(vy, vx) - self.offset
            dist = math.hypot(vx, vy) / self.rho
            tx, ty = self.pos[0] + dist * math.cos(angle), self.pos[1] + dist * math.sin(angle)
            if math.hypot(tx, ty) <= radius and (best is None or dist < best[1]):
                best = (angle, dist)
        if best:
            return best[0], min(step, max(best[1], 0.4 * step)), "radar"

        if self.home_distance > 0.3 * radius:
            angle = math.atan2(-self.pos[1], -self.pos[0])
            return angle, min(step, self.home_distance), "home"

        for _ in range(12):
            angle = self.rng.uniform(0, 2 * math.pi)
            length = 0.6 * step
            if math.hypot(self.pos[0] + length * math.cos(angle), self.pos[1] + length * math.sin(angle)) <= 0.9 * radius:
                return angle, length, "wander"
        return math.pi / 2, 0.6 * step, "wander"

    def next_move(self, shape, dots, step, radius, excludes=()):
        """Plan a move and turn it into a clickable point; None if no safe point exists."""
        h, w = shape[:2]
        scale = h / REF_HEIGHT
        angle, length, reason = self.plan(dots, step, radius)
        px, py = w * PLAYER[0], h * PLAYER[1]
        x0, y0, x1, y1 = GROUND[0] * w, GROUND[1] * h, GROUND[2] * w, GROUND[3] * h

        for _ in range(7):  # shrink the step until the point lies on usable ground
            x = px + math.cos(angle) * length * scale
            y = py - math.sin(angle) * length * scale * PERSPECTIVE
            on_ui = any(l * w <= x <= r * w and t * h <= y <= b * h for l, t, r, b in excludes)
            if x0 <= x <= x1 and y0 <= y <= y1 and not on_ui:
                self.pos[0] += math.cos(angle) * length
                self.pos[1] += math.sin(angle) * length
                return Move(angle, length, (int(x), int(y)), reason)
            length *= 0.75
        return None

    # -- learning --------------------------------------------------------
    def observe(self, before, after, move):
        """Learn radar rotation and scale from how the dots shifted after `move`.

        The character moves one way, the dots slide the opposite way on the radar,
        so the shift of the whole dot field gives the movement as the radar sees it.
        """
        shifts = []
        for bx, by in before:
            near = min(after, key=lambda d: (d[0] - bx) ** 2 + (d[1] - by) ** 2, default=None)
            if near and math.hypot(near[0] - bx, near[1] - by) <= MATCH_RADIUS:
                shifts.append((bx - near[0], by - near[1]))  # movement as seen on the radar
        if len(shifts) < 2:
            return False
        mx = sorted(s[0] for s in shifts)[len(shifts) // 2]   # median: robust to walking monsters
        my = sorted(s[1] for s in shifts)[len(shifts) // 2]
        magnitude = math.hypot(mx, my)
        if magnitude < MIN_SHIFT:
            return False  # we did not really move (blocked, or the click missed the ground)

        measured_offset = math.atan2(my, mx) - move.angle
        if self.calibrated:
            # The character may have been blocked: correct the dead-reckoned position with what really moved.
            actual = min(move.length, magnitude / self.rho)
            self.pos[0] += math.cos(move.angle) * (actual - move.length)
            self.pos[1] += math.sin(move.angle) * (actual - move.length)
            self.offset = _circ_mean(self.offset, measured_offset, 0.35)
            self.rho = 0.7 * self.rho + 0.3 * (magnitude / max(move.length, 1.0))
        else:
            self.offset = measured_offset
            self.rho = magnitude / max(move.length, 1.0)
            self.calibrated = True
        return True
