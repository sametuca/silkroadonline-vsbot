"""The bot against a tiny fake game: labels on screen plus the game's target window."""

import math
import time

import pytest

from conftest import add_panel, make_scene
from srbot import engine, inputs, winutil
from srbot.config import Config

A, B, C = (380, 300), (300, 260), (150, 200)     # label baselines; A is nearest to the player, C the farthest


class World:
    """Monsters stand where they are. Corpses keep their label and show an empty bar when selected."""

    def __init__(self, labels, corpses=(), lag=0.0, panel=True, kills_after=3, band=None):
        self.labels, self.corpses = list(labels), set(corpses)
        self.band = band  # (min, max) px below the label baseline that actually hit the sprite; None = any click hits
        self.raw_clicks = []
        self.lag, self.panel, self.kills_after = lag, panel, kills_after
        self.selected = self.previous = None
        self.selected_at = 0.0
        self.presses = self.total_presses = 0
        self.clicks = []

    def click(self, x, y):
        index = min(range(len(self.labels)), key=lambda i: math.dist((x, y), (self.labels[i][0] + 30, self.labels[i][1] + 21)))
        self.raw_clicks.append((x, y))
        if self.band and not self.band[0] <= y - self.labels[index][1] <= self.band[1]:
            return  # the click missed the sprite: nothing gets selected
        self.clicks.append(index)
        self.previous, self.selected, self.selected_at, self.presses = self.selected, index, time.time(), 0

    def press(self, _key):
        self.presses += 1
        self.total_presses += 1

    def _shown_fill(self):
        shown = self.selected
        if self.lag and self.previous is not None and time.time() - self.selected_at < self.lag:
            shown = self.previous  # the window still shows the previous target for a moment
        if shown is None:
            return None
        if shown in self.corpses:
            return 0.0
        fill = 0.9 - 0.9 * self.presses / self.kills_after
        if fill <= 0 and shown == self.selected:
            self.corpses.add(shown)  # it died
            return 0.0
        return max(fill, 0.05)

    def frame(self):
        img = make_scene([("Mangyang", x, y) for x, y in self.labels])
        fill = self._shown_fill() if self.panel else None
        return img if fill is None else add_panel(img, fill)


class Screen:
    world = None

    def grab_bgr(self, rect):
        return Screen.world.frame()

    def close(self):
        pass


@pytest.fixture
def play(monkeypatch):
    def run(world, seconds, **cfg_kw):
        Screen.world = world
        monkeypatch.setattr(engine, "ScreenGrabber", Screen)
        monkeypatch.setattr(winutil, "get_window_client_rect_on_screen", lambda h: (0, 0, 802, 632))
        monkeypatch.setattr(winutil, "is_window_valid", lambda h: True)
        monkeypatch.setattr(winutil, "is_foreground", lambda h: True)
        monkeypatch.setattr(winutil, "needs_admin_for", lambda h: False)
        monkeypatch.setattr(inputs, "click_at", lambda x, y: world.click(x, y) or True)
        monkeypatch.setattr(inputs, "press_key", lambda k: world.press(k) or True)
        cfg = Config(monsters=["Mangyang"], excludes=[], attack_keys=["1"], attack_interval=0.05,
                     scan_interval=0.02, detector="ocr", roam=False, **cfg_kw)
        messages = []
        bot = engine.BotEngine(cfg, hwnd=1, on_log=messages.append)
        bot.start()
        deadline = time.time() + seconds
        while time.time() < deadline and bot.kills < 1:
            time.sleep(0.05)
        time.sleep(0.5)  # let it carry on: it must not go back to the corpses
        bot.stop()
        bot.join(5)
        return bot, messages
    return run


def test_dead_monsters_are_skipped_and_the_live_one_is_hit(play):
    world = World([A, B, C], corpses={0, 1})
    bot, messages = play(world, 12)
    assert world.clicks[:3] == [0, 1, 2]           # two corpses, then the live monster, in one go
    assert bot.kills == 1
    assert world.clicks.count(0) == 1 and world.clicks.count(1) == 1   # corpses are never clicked twice
    assert sum("zaten ölüydü" in m for m in messages) >= 2


def test_a_lone_corpse_is_clicked_once_not_forever(play):
    world = World([A], corpses={0})
    bot, _ = play(world, 1.5)
    assert world.clicks == [0] and bot.kills == 0


def test_stale_window_after_a_click_does_not_make_a_live_monster_look_dead(play):
    world = World([A, B], corpses={0}, lag=0.15)
    bot, _ = play(world, 12)
    assert bot.kills == 1
    spots = [(round(x), round(y)) for x, y, _ in bot.zones]
    assert len(spots) >= 1 and all(abs(x - (A[0] + 30)) < 8 for x, _ in spots[:1])  # only the corpse was remembered
    assert world.clicks[:2] == [0, 1]


def test_a_fight_ends_the_moment_the_bar_empties(play):
    world = World([A], kills_after=3)
    started = time.time()
    bot, messages = play(world, 12)
    assert bot.kills == 1 and any("öldü" in m for m in messages)
    assert world.total_presses >= 3
    assert time.time() - started < 6             # no 30 s time-out wait, no 3-scan label wait


def test_unreadable_target_window_falls_back_to_name_labels(play, monkeypatch, tmp_path):
    monkeypatch.setattr(engine, "data_path", lambda *parts: str(tmp_path.joinpath(*parts)))
    world = World([A, B, C], panel=False)
    bot, messages = play(world, 12, attack_timeout=0.25)
    assert bot.panel_ok is False
    assert any("Hedef penceresi okunamadı" in m for m in messages)
    # evidence for diagnosing it: the measurements are logged and the frame is saved
    assert any("Kare kaydedildi" in m for m in messages)
    assert list((tmp_path / "debug").glob("target_window_*.png"))


def test_a_click_that_misses_the_sprite_is_retried_lower(play):
    world = World([A], band=(28, 60))           # the default click height (21 px below the baseline) misses
    bot, messages = play(world, 12)
    assert bot.panel_ok is True and bot.kills == 1
    assert len(world.raw_clicks) >= 3 and len(world.clicks) >= 1
    ys = [y for _, y in world.raw_clicks[:3]]
    assert ys[0] < ys[1] + 1 or ys[1] < ys[0]   # three different heights were tried
    assert len(set(ys)) == 3


# -- label-based mode (target window unreadable) ------------------------------------
class TimedScreen:
    """One monster label; `visible(seconds_since_start)` says when it is on screen. No target window."""

    start = 0.0
    visible = staticmethod(lambda s: True)

    def grab_bgr(self, rect):
        shown = TimedScreen.visible(time.time() - TimedScreen.start)
        return make_scene([("Mangyang", *A)] if shown else [])

    def close(self):
        pass


def _run_label_mode(monkeypatch, visible, seconds, keys):
    TimedScreen.start, TimedScreen.visible = time.time(), staticmethod(visible)
    pressed = []
    monkeypatch.setattr(engine, "ScreenGrabber", TimedScreen)
    monkeypatch.setattr(winutil, "get_window_client_rect_on_screen", lambda h: (0, 0, 802, 632))
    monkeypatch.setattr(winutil, "is_window_valid", lambda h: True)
    monkeypatch.setattr(winutil, "is_foreground", lambda h: True)
    monkeypatch.setattr(winutil, "needs_admin_for", lambda h: False)
    monkeypatch.setattr(inputs, "click_at", lambda x, y: True)
    monkeypatch.setattr(inputs, "press_key", lambda k: pressed.append(k) or True)
    cfg = Config(monsters=["Mangyang"], excludes=[], attack_keys=keys, attack_interval=0.1, scan_interval=0.02,
                 detector="ocr", roam=False)
    messages = []
    bot = engine.BotEngine(cfg, hwnd=1, on_log=messages.append)
    bot.start()
    deadline = time.time() + seconds
    while time.time() < deadline and bot.kills < 1:
        time.sleep(0.05)
    bot.stop()
    bot.join(5)
    return bot, pressed, messages


def test_label_mode_rotates_through_all_attack_keys(monkeypatch):
    bot, pressed, messages = _run_label_mode(monkeypatch, lambda s: s < 1.0, 12, ["1", "2", "3", "4"])
    assert bot.kills == 1
    assert {"1", "2", "3", "4"} <= set(pressed)                  # every key was used, not just the first
    assert pressed[:4] == ["1", "2", "3", "4"]
    assert any("1, 2, 3, 4" in m for m in messages)


def test_a_label_that_blinks_is_not_a_kill(monkeypatch):
    # the label is hidden for 0.6 s in the middle of the fight (an OCR miss / the monster ran past): not dead
    bot, pressed, _ = _run_label_mode(monkeypatch, lambda s: not (0.5 < s < 1.1) and s < 3.0, 12, ["1", "2"])
    assert bot.kills == 1
    assert len(pressed) >= 10                                    # it kept attacking through the blink
