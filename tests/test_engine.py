"""Drive the hunt loop with a fake screen and fake input: no game needed."""

import time

from srbot import engine, inputs, winutil
from srbot.config import Config


class FakeGrabber:
    """Shows the monster scene for the first N grabs, then an empty one (monster died)."""

    def __init__(self, with_monster, empty, alive_grabs):
        self.frames, self.calls = (with_monster, empty), 0
        self.alive_grabs = alive_grabs

    def grab_bgr(self, rect):
        self.calls += 1
        return self.frames[0] if self.calls <= self.alive_grabs else self.frames[1]

    def close(self):
        pass


def test_hunt_cycle(monkeypatch, scene):
    log = []
    monkeypatch.setattr(engine, "ScreenGrabber", lambda: FakeGrabber(scene([("Mangyang", 300, 300)]), scene([]), 8))
    monkeypatch.setattr(winutil, "get_window_client_rect_on_screen", lambda h: (0, 0, 802, 632))
    monkeypatch.setattr(winutil, "is_window_valid", lambda h: True)
    monkeypatch.setattr(winutil, "is_foreground", lambda h: True)
    monkeypatch.setattr(inputs, "click_at", lambda x, y: log.append(("click", x, y)) or True)
    monkeypatch.setattr(inputs, "press_key", lambda k: log.append(("key", k)) or True)

    cfg = Config(monsters=["Mangyang"], excludes=[], attack_keys=["1", "2"], attack_interval=0.05,
                 scan_interval=0.02, loot_key="z", loot_delay=0.05, detector="ocr")
    bot = engine.BotEngine(cfg, hwnd=1)
    bot.start()
    deadline = time.time() + 30
    while ("key", "z") not in log and time.time() < deadline:  # kill is counted before looting
        time.sleep(0.1)
    bot.stop()
    bot.join(5)

    assert bot.kills == 1
    assert log[0][0] == "click"
    assert ("key", "1") in log and ("key", "2") in log
    assert log[-1] == ("key", "z")  # looted after the kill


def _patch_screen(monkeypatch, scene, log, click_ok=True):
    monkeypatch.setattr(engine, "ScreenGrabber", lambda: FakeGrabber(scene([("Mangyang", 300, 300)]), scene([]), 8))
    monkeypatch.setattr(winutil, "get_window_client_rect_on_screen", lambda h: (0, 0, 802, 632))
    monkeypatch.setattr(winutil, "is_window_valid", lambda h: True)
    monkeypatch.setattr(winutil, "is_foreground", lambda h: True)
    monkeypatch.setattr(inputs, "click_at", lambda x, y: log.append(("click", x, y)) or click_ok)
    monkeypatch.setattr(inputs, "press_key", lambda k: log.append(("key", k)) or True)


def _run_briefly(cfg, seconds=3):
    messages = []
    bot = engine.BotEngine(cfg, hwnd=1, on_log=messages.append)
    bot.start()
    bot.join(seconds)
    bot.stop()
    bot.join(5)
    return messages


def test_refuses_to_run_when_game_is_elevated_and_we_are_not(monkeypatch, scene):
    log = []
    _patch_screen(monkeypatch, scene, log)
    monkeypatch.setattr(winutil, "needs_admin_for", lambda h: True)
    cfg = Config(monsters=["Mangyang"], excludes=[], detector="ocr", scan_interval=0.02)
    messages = _run_briefly(cfg)
    assert log == []  # nothing was sent
    assert any("yönetici" in m for m in messages)


def test_rejected_click_is_reported_not_silent(monkeypatch, scene):
    log = []
    _patch_screen(monkeypatch, scene, log, click_ok=False)
    monkeypatch.setattr(winutil, "needs_admin_for", lambda h: False)
    cfg = Config(monsters=["Mangyang"], excludes=[], detector="ocr", scan_interval=0.02, attack_keys=["1"])
    messages = _run_briefly(cfg)
    assert any("reddedildi" in m for m in messages)
    assert ("key", "1") not in log  # no attack keys after a failed click
