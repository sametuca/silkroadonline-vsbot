import random
import time

from srbot import engine, inputs, winutil
from srbot.config import DEFAULT_EXCLUDES, Config
from srbot.roam import GROUND, Roamer

SHAPE = (632, 802, 3)


def test_points_stay_on_the_ground_and_off_the_ui():
    roamer = Roamer(random.Random(3))
    h, w = SHAPE[:2]
    for _ in range(300):
        x, y = roamer.next_point(SHAPE, 200, DEFAULT_EXCLUDES)
        assert GROUND[0] * w <= x <= GROUND[2] * w and GROUND[1] * h <= y <= GROUND[3] * h
        assert not any(l * w <= x <= r * w and t * h <= y <= b * h for l, t, r, b in DEFAULT_EXCLUDES)


def test_walk_explores_in_every_direction():
    roamer = Roamer(random.Random(5))
    xs = {roamer.next_point(SHAPE, 200, DEFAULT_EXCLUDES)[0] // 100 for _ in range(200)}
    assert len(xs) >= 3  # not stuck in one spot


def test_step_scales_with_window_size():
    far = Roamer(random.Random(1)).next_point((1264, 1604, 3), 200)
    near = Roamer(random.Random(1)).next_point(SHAPE, 200)
    cx_far, cx_near = 1604 * 0.5, 802 * 0.5
    assert abs(far[0] - cx_far) > abs(near[0] - cx_near)


class EmptyScreen:
    def grab_bgr(self, rect):
        return EmptyScreen.frame

    def close(self):
        pass


def _setup(monkeypatch, scene, log):
    EmptyScreen.frame = scene([])
    monkeypatch.setattr(engine, "ScreenGrabber", EmptyScreen)
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


def test_bot_walks_when_no_monster_is_visible(monkeypatch, scene):
    log = []
    _setup(monkeypatch, scene, log)
    cfg = Config(monsters=["Mangyang"], excludes=[], detector="ocr", scan_interval=0.02,
                 roam_after=0.1, roam_wait=0.05)
    messages = _run(cfg, 1.5)
    clicks = [e for e in log if e[0] == "click"]
    assert len(clicks) >= 2
    assert all(e[0] == "click" for e in log)  # walking only: no attack keys
    assert any("gezin" in m for m in messages)


def test_roaming_can_be_turned_off(monkeypatch, scene):
    log = []
    _setup(monkeypatch, scene, log)
    cfg = Config(monsters=["Mangyang"], excludes=[], detector="ocr", scan_interval=0.02,
                 roam=False, roam_after=0.05)
    _run(cfg, 0.8)
    assert log == []
