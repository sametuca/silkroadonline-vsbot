"""Hunt loop: SCANNING -> CONFIRMING -> ATTACKING (-> ROAMING when idle), on a worker thread."""

import math
import threading
import time
from enum import Enum

from . import detect, inputs, radar, winutil
from .i18n import t
from .capture import ScreenGrabber
from .roam import PLAYER, Roamer

class State(str, Enum):
    IDLE = "Beklemede"
    SCANNING = "Canavar aranıyor"
    CONFIRMING = "Hedef doğrulanıyor"
    ATTACKING = "Saldırıyor"
    ROAMING = "Canavar aranıyor (geziyor)"


class BotEngine(threading.Thread):
    """Callbacks (all called from the worker thread):
    on_log(str), on_state(State), on_frame(bgr_frame, detections)."""

    def __init__(self, cfg, hwnd, on_log=None, on_state=None, on_frame=None, recorder=None, on_roam=None):
        super().__init__(daemon=True)
        self.cfg, self.hwnd = cfg, hwnd
        self.on_log = on_log or (lambda m: None)
        self.on_state = on_state or (lambda s: None)
        self.on_frame = on_frame or (lambda f, d: None)
        self.on_roam = on_roam or (lambda point: None)
        self.target_pos = None  # click position of the monster being attacked (read by the overlay)
        self._stop_evt = threading.Event()
        self.recorder = recorder
        self.kills = 0
        self._last_idle_log = 0.0
        self._idle_since = None
        self._roam_reason = None
        self.roamer = Roamer()

    def stop(self):
        self._stop_evt.set()

    # -- helpers ---------------------------------------------------------
    def _sleep(self, seconds):
        self._stop_evt.wait(seconds)

    def _grab(self, grabber):
        rect = winutil.get_window_client_rect_on_screen(self.hwnd)
        if not rect:
            return None, None
        return grabber.grab_bgr(rect), rect

    def _focus(self):
        if not winutil.is_foreground(self.hwnd):
            winutil.bring_window_to_front(self.hwnd)
            self._sleep(0.15)
        return winutil.is_foreground(self.hwnd)

    def _scan(self, grabber):
        frame, rect = self._grab(grabber)
        if frame is None:
            return None, None, []
        dets = detect.detect(frame, self.cfg)
        self.on_frame(frame, dets)
        if self.recorder:
            self.recorder.maybe_save(frame, dets)
        return frame, rect, dets

    def _nearest(self, dets, shape, avoid):
        h, w = shape[:2]
        px, py = w * PLAYER[0], h * PLAYER[1]  # where the character stands on screen
        ok = [d for d in dets if not any(math.dist(d.click, a) < 40 for a in avoid)]
        return min(ok, key=lambda d: math.dist(d.click, (px, py)), default=None)

    def _press(self, key):
        self._focus()
        if not inputs.press_key(key):
            self.on_log(t("bot_key_failed", key=key))
            return False
        return True

    # -- main loop -------------------------------------------------------
    def run(self):
        grabber = ScreenGrabber()
        avoid = []  # recently failed click spots
        try:
            if winutil.needs_admin_for(self.hwnd):
                self.on_log(t("admin_hint"))
                return
            self.on_log(t("bot_started"))
            if not self._focus():
                self.on_log(t("bot_no_focus"))
            while not self._stop_evt.is_set():
                if not winutil.is_window_valid(self.hwnd):
                    self.on_log(t("bot_window_closed"))
                    break
                self.on_state(State.SCANNING)
                frame, rect, dets = self._scan(grabber)
                target = self._nearest(dets, frame.shape, avoid) if frame is not None else None
                if target is None:
                    avoid = avoid[-3:]
                    if frame is not None and self._maybe_roam(grabber, frame, rect):
                        continue
                    self._log_idle()
                    self._sleep(self.cfg.scan_interval)
                    continue
                # A monster here means this is farmable ground: roaming limits are measured from this spot.
                self.roamer.reset_home()
                self._idle_since, self._roam_reason = None, None

                if not self._confirm(grabber, rect, target):
                    continue
                try:
                    self._hunt(grabber, rect, target, avoid)
                finally:
                    self.target_pos = None
        except Exception as exc:  # keep the GUI informed instead of dying silently
            self.on_log(t("bot_error", err=exc))
        finally:
            grabber.close()
            self.on_state(State.IDLE)
            self.on_log(t("bot_stopped"))

    def _maybe_roam(self, grabber, frame, rect):
        """Nothing to hit for a while: walk toward the radar's monster dots (within the leash) and look again."""
        if not self.cfg.roam:
            return False
        now = time.time()
        if self._idle_since is None:
            self._idle_since = now
        if now - self._idle_since < self.cfg.roam_after or not self._focus():
            return False
        self.on_state(State.ROAMING)
        before = radar.read_dots(frame)
        move = self.roamer.next_move(frame.shape, before, self.cfg.roam_step,
                                     self.cfg.roam_radius * self.cfg.roam_step)
        if move is None:
            return False
        if move.reason != self._roam_reason:
            self._roam_reason = move.reason
            self.on_log(t({"radar": "roam_radar", "home": "roam_home", "wander": "roam_wander"}[move.reason],
                          n=len(before)))
        if not inputs.click_at(rect[0] + move.point[0], rect[1] + move.point[1]):
            self.on_log(t("roam_rejected"))
            self._idle_since = now
            return False
        self.on_roam(move.point)
        self._sleep(self.cfg.roam_wait)
        after_frame, _ = self._grab(grabber)
        if after_frame is not None:
            self.roamer.observe(before, radar.read_dots(after_frame), move)
        return True

    def _log_idle(self):
        now = time.time()
        if now - self._last_idle_log > 10:
            self._last_idle_log = now
            self.on_log(t("bot_idle"))

    def _confirm(self, grabber, rect, target):
        """The same label must show up again before we click (filters one-frame OCR noise).

        Tolerates a missed read: one extra attempt is allowed, and the label may have
        moved a little (monsters walk).
        """
        self.on_state(State.CONFIRMING)
        needed = max(0, self.cfg.confirm_frames - 1)
        attempts = needed + 1 if needed else 0
        radius = 90 * rect_scale(rect)
        hits = 0
        for _ in range(attempts):
            self._sleep(self.cfg.scan_interval)
            if self._stop_evt.is_set():
                return False
            _, _, dets = self._scan(grabber)
            if any(d.name == target.name and math.dist(d.click, target.click) < radius for d in dets):
                hits += 1
                if hits >= needed:
                    return True
        return needed == 0

    def _hunt(self, grabber, rect, target, avoid):
        if not self._focus():
            self.on_log(t("bot_retry_focus"))
            self._sleep(1.0)
            return
        pos = target.click
        self.on_log(t("bot_target", name=target.name, pos=pos))
        if not inputs.click_at(rect[0] + pos[0], rect[1] + pos[1]):
            self.on_log(t("bot_click_rejected"))
            self._sleep(1.0)
            return

        self.on_state(State.ATTACKING)
        self.target_pos = pos
        radius = 110 * rect_scale(rect)
        started = last_press = time.time()
        misses = 0
        key_index = 0
        first_key = True
        while not self._stop_evt.is_set():
            now = time.time()
            if now - last_press >= self.cfg.attack_interval and self.cfg.attack_keys:
                key = self.cfg.attack_keys[key_index % len(self.cfg.attack_keys)]
                if self._press(key) and first_key:
                    self.on_log(t("bot_key_sent", key=key))
                    first_key = False
                key_index += 1
                last_press = now
            _, _, dets = self._scan(grabber)
            same = [d for d in dets if d.name == target.name and math.dist(d.click, pos) < radius]
            if same:
                misses = 0
                pos = min(same, key=lambda d: math.dist(d.click, pos)).click
                self.target_pos = pos
            else:
                misses += 1
                if misses >= 3:
                    self.kills += 1
                    self.on_log(t("bot_killed", name=target.name, n=self.kills))
                    return
            if now - started > self.cfg.attack_timeout:
                self.on_log(t("bot_timeout"))
                avoid.append(pos)
                return
            self._sleep(self.cfg.scan_interval)


def rect_scale(rect):
    return (rect[3] - rect[1]) / detect.REF_HEIGHT

