import math
import random
import time

import pytest

from conftest import add_radar, make_scene
from srbot import engine, inputs, radar, winutil
from srbot.config import Config
from srbot.roam import GROUND, ROAM_AVOID, Roamer

SHAPE = (632, 802, 3)
STEP, RADIUS = 200, 1200


# -- radar reading -----------------------------------------------------------
def test_reads_the_red_monster_dots_from_a_real_radar():
    dots = radar.read_dots(add_radar(make_scene([])))
    expected = [(19, 18), (-24, -12), (6, -14), (39, -15), (-19, -28)]  # px from the arrow, y up
    assert len(dots) == len(expected)
    for ex, ey in expected:
        assert any(math.hypot(x - ex, y - ey) < 3 for x, y in dots), (ex, ey, dots)


def test_no_dots_on_an_empty_radar_area():
    assert radar.read_dots(make_scene([])) == []


# -- planning ----------------------------------------------------------------
def test_heads_for_the_nearest_dot():
    angle, length, reason = Roamer().plan([(0, 30), (60, 0)], STEP, RADIUS)
    assert reason == "radar" and angle == pytest.approx(math.pi / 2)
    assert length <= STEP


def test_dots_beyond_the_leash_are_ignored():
    r = Roamer(random.Random(1))
    far = [(0, 48)]                       # 48 / 0.025 = 1920 reference px away
    assert r.plan(far, STEP, RADIUS)[2] != "radar"
    assert r.plan(far, STEP, 3000)[2] == "radar"


def test_walks_home_when_the_radar_is_empty():
    r = Roamer()
    r.pos = [600.0, 0.0]
    angle, length, reason = r.plan([], STEP, RADIUS)
    assert reason == "home" and abs(abs(angle) - math.pi) < 1e-6 and length == STEP


def test_wandering_never_leaves_the_farming_area():
    r, rng = Roamer(random.Random(4)), random.Random(9)
    for _ in range(500):
        dots = [] if rng.random() < 0.7 else [(rng.uniform(-48, 48), rng.uniform(-30, 30))]
        r.next_move(SHAPE, dots, STEP, RADIUS, ROAM_AVOID)
        assert r.home_distance <= RADIUS * 1.05


def test_click_points_stay_on_the_ground_and_off_the_ui():
    r, rng = Roamer(random.Random(3)), random.Random(2)
    h, w = SHAPE[:2]
    for _ in range(300):
        dots = [(rng.uniform(-48, 48), rng.uniform(-48, 48)) for _ in range(rng.randint(0, 4))]
        move = r.next_move(SHAPE, dots, STEP, RADIUS, ROAM_AVOID)
        assert move is not None
        x, y = move.point
        assert GROUND[0] * w <= x <= GROUND[2] * w and GROUND[1] * h <= y <= GROUND[3] * h
        assert not any(l * w <= x <= rr * w and t * h <= y <= b * h for l, t, rr, b in ROAM_AVOID)


def test_step_scales_with_window_size():
    big = Roamer(random.Random(1)).next_move((1264, 1604, 3), [(0, 40)], STEP, RADIUS)
    small = Roamer(random.Random(1)).next_move(SHAPE, [(0, 40)], STEP, RADIUS)
    assert abs(big.point[1] - 1264 * 0.52) > abs(small.point[1] - 632 * 0.52)


# -- learning the radar's orientation -----------------------------------------
def _simulate_step(r, rotation, rho, world_dots, move):
    """Dots on the radar after the character walks `move`, for a map rotated by `rotation`."""
    walk = move.angle + rotation                       # direction of the walk as drawn on the radar
    shift = (-math.cos(walk) * move.length * rho, -math.sin(walk) * move.length * rho)
    return [(x + shift[0], y + shift[1]) for x, y in world_dots]


@pytest.mark.parametrize("rotation", [0.0, math.pi / 2, -2.0, math.pi])
def test_learns_how_the_radar_is_rotated(rotation):
    r = Roamer(random.Random(1))
    dots = [(10, 20), (-25, 5), (30, -15), (-10, -30)]
    move = r.next_move(SHAPE, dots, STEP, 100000)
    after = _simulate_step(r, rotation, 0.04, dots, move)
    assert r.observe(dots, after, move) is True
    assert math.cos(r.offset - rotation) > 0.99          # same angle modulo 2*pi
    assert r.rho == pytest.approx(0.04, rel=0.01)


def test_a_blocked_character_does_not_teach_anything():
    r = Roamer(random.Random(1))
    dots = [(10, 20), (-25, 5), (30, -15)]
    move = r.next_move(SHAPE, dots, STEP, 100000)
    assert r.observe(dots, list(dots), move) is False
    assert not r.calibrated


def test_calibration_steers_toward_a_dot_on_a_rotated_radar():
    r = Roamer(random.Random(1))
    r.offset = math.pi / 2                                # radar "up" is ground-forward minus 90 degrees
    angle, _, reason = r.plan([(40, 0)], STEP, 100000)    # a dot due east on the radar
    # radar angle 0 minus the 90 degree offset: the monster is to the ground-frame south
    assert reason == "radar" and angle == pytest.approx(-math.pi / 2)


# -- the bot ------------------------------------------------------------------
class FrameGrabber:
    frame = None

    def grab_bgr(self, rect):
        return FrameGrabber.frame

    def close(self):
        pass


def _setup(monkeypatch, frame, log):
    FrameGrabber.frame = frame
    monkeypatch.setattr(engine, "ScreenGrabber", FrameGrabber)
    monkeypatch.setattr(winutil, "get_window_client_rect_on_screen", lambda h: (0, 0, 802, 632))
    monkeypatch.setattr(winutil, "is_window_valid", lambda h: True)
    monkeypatch.setattr(winutil, "is_foreground", lambda h: True)
    monkeypatch.setattr(winutil, "needs_admin_for", lambda h: False)
    monkeypatch.setattr(inputs, "click_at", lambda x, y: log.append(("click", x, y)) or True)
    monkeypatch.setattr(inputs, "press_key", lambda k: log.append(("key", k)) or True)


def _run(cfg, seconds):
    messages = []
    bot = engine.BotEngine(cfg, hwnd=1, on_log=messages.append)
    bot.start()
    time.sleep(seconds)
    bot.stop()
    bot.join(5)
    return messages


def test_bot_walks_toward_the_nearest_radar_dot(monkeypatch):
    log = []
    _setup(monkeypatch, add_radar(make_scene([])), log)
    cfg = Config(monsters=["Mangyang"], excludes=[], detector="ocr", scan_interval=0.02,
                 roam_after=0.05, roam_wait=0.05)
    messages = _run(cfg, 1.2)
    clicks = [e for e in log if e[0] == "click"]
    assert len(clicks) >= 2 and all(e[0] == "click" for e in log)  # walking only: no attack keys
    # nearest dot is below-right of the arrow, so the click lands below the player (y grows downward)
    assert clicks[0][2] > 632 * 0.52
    assert any("Radarda" in m for m in messages)


def test_bot_stays_near_home_when_the_radar_is_empty(monkeypatch):
    log = []
    _setup(monkeypatch, make_scene([]), log)
    cfg = Config(monsters=["Mangyang"], excludes=[], detector="ocr", scan_interval=0.02,
                 roam_after=0.05, roam_wait=0.03)
    messages = _run(cfg, 1.2)
    assert any("Radar boş" in m for m in messages)
    assert sum(1 for e in log if e[0] == "click") >= 2


def test_roaming_can_be_turned_off(monkeypatch):
    log = []
    _setup(monkeypatch, add_radar(make_scene([])), log)
    cfg = Config(monsters=["Mangyang"], excludes=[], detector="ocr", scan_interval=0.02,
                 roam=False, roam_after=0.05)
    _run(cfg, 0.8)
    assert log == []
