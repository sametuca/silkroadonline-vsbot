"""Hunt loop on a worker thread, fed by a scanner thread.

A second thread scans the screen non-stop (about ten times a second). The hunt
loop therefore never waits for a scan: when a monster dies, the next target is
picked from a scan that is only a moment old, and the dying monster's label is
followed during the whole fight so its corpse (dead monsters keep their name
label) is known and never clicked.

Click a monster's name label and attack at once: the first attack key goes out
right after the click, and the check that the selection worked is made WHILE
attacking, never as a wait in front of it. The check reads the game's own target
window (see target.py):

* empty bar and never alive since the click -> it was a corpse: ignore its spot;
* bar filled and then emptied (or the window vanished) -> killed: next monster;
* the window cannot be seen at all (interface hidden, other skin) -> "blind"
  fights: attack for a short, fixed time, then move on.
"""

import math
import os
import threading
import time
from dataclasses import dataclass
from enum import Enum

import cv2
from rapidfuzz import fuzz

from . import detect, inputs, radar, winutil
from .capture import ScreenGrabber
from .i18n import t
from .paths import data_path
from .roam import PLAYER, Roamer
from .target import read_panel

POLL = 0.05             # seconds between looks at the game while fighting
CORPSE_CONFIRM = 0.25   # an empty bar must persist this long before "corpse" (the window lags after a click)
PANEL_GRACE = 0.8       # blind-fight check: how long without a target window before it counts as unreadable
SELECT_GRACE = 0.6      # when the window is known to work it must show up this soon after a click, else the click missed
CORPSE_TTL = 60.0       # seconds a corpse's label spot is ignored
ZONE_RADIUS = 45        # px (at 632 px window height) around a remembered spot
STALL_SECONDS = 12.0    # a fight whose target loses no health for this long is abandoned
PANEL_FAILS_TO_GIVE_UP = 3
CLICK_HEIGHTS = (1.0, 0.45, 1.65)  # click offsets below the label, as multiples of the configured one
MAX_DEBUG_FRAMES = 6
SCAN_PAUSE = 0.01       # the scanner thread's pause between scans
SCAN_WAIT = 2.0         # longest wait for a new scan before the hunt loop looks around again


@dataclass
class Scan:
    id: int
    shape: tuple
    rect: tuple
    scale: float
    frame: object
    dets: list


class State(str, Enum):
    IDLE = "Beklemede"
    SCANNING = "Canavar aranıyor"
    ATTACKING = "Saldırıyor"
    ROAMING = "Canavar aranıyor (geziyor)"


class BotEngine(threading.Thread):
    """Callbacks (called from the worker threads):
    on_log(str), on_state(State), on_frame(bgr_frame, detections), on_roam((x, y))."""

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
        self.zones = []          # [(x, y, expires_at)] label spots to ignore: corpses, unreachable monsters
        self.panel_ok = None     # None = not known yet, True = target window readable, False = fight blind
        self._panel_misses = 0
        self._height = 0         # index into CLICK_HEIGHTS: advances when a click selects nothing, stays when one works
        self._debug_saved = 0
        self._scale = 1.0
        self._latest = None      # newest Scan from the scanner thread
        self._scan_cond = threading.Condition()

    def stop(self):
        self._stop_evt.set()
        with self._scan_cond:
            self._scan_cond.notify_all()

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

    def _mark(self, pos, ttl):
        """Ignore the label at `pos` for `ttl` seconds."""
        self.zones.append((pos[0], pos[1], time.time() + ttl))

    def _in_zone(self, pos):
        now = time.time()
        self.zones = [z for z in self.zones if z[2] > now]
        radius = ZONE_RADIUS * self._scale
        return any(math.dist(pos, (z[0], z[1])) < radius for z in self.zones)

    def _candidates(self, dets, shape):
        """Monsters worth clicking, nearest to the player first; ignored spots are left out."""
        h, w = shape[:2]
        px, py = w * PLAYER[0], h * PLAYER[1]  # where the character stands on screen
        ok = [d for d in dets if not self._in_zone(d.click)]
        return sorted(ok, key=lambda d: math.dist(d.click, (px, py)))

    def _press(self, key):
        self._focus()
        if not inputs.press_key(key):
            self.on_log(t("bot_key_failed", key=key))
            return False
        return True

    def _click_point(self, target, height):
        """Where to click `target`; `height` scales how far below its label (or how low on its body)."""
        x0, y0, w, h = target.box
        if target.source == "model":
            return target.click[0], int(target.click[1] + (height - 1.0) * 0.25 * h)
        return x0 + w // 2, int(y0 + h + self.cfg.click_offset * self._scale * height)

    # -- the scanner thread ---------------------------------------------------
    def _scanner(self):
        """Scan the screen over and over; the hunt loop only ever reads the newest result."""
        grabber = ScreenGrabber()  # mss handles are per thread
        scan_id, warned = 0, False
        try:
            while not self._stop_evt.is_set():
                try:
                    frame, rect = self._grab(grabber)
                    if frame is not None:
                        dets = detect.detect(frame, self.cfg)
                        self.on_frame(frame, dets)
                        if self.recorder:
                            self.recorder.maybe_save(frame, dets)
                        scan_id += 1
                        scan = Scan(scan_id, frame.shape, rect, rect_scale(rect), frame, dets)
                        with self._scan_cond:
                            self._latest = scan
                            self._scan_cond.notify_all()
                except Exception as exc:  # report once, keep scanning
                    if not warned:
                        warned = True
                        self.on_log(t("bot_error", err=exc))
                    self._sleep(0.2)
                self._sleep(SCAN_PAUSE)
        finally:
            grabber.close()

    def _wait_scan(self, after_id):
        """The newest scan if it is newer than `after_id`, else wait briefly for one."""
        with self._scan_cond:
            self._scan_cond.wait_for(
                lambda: self._stop_evt.is_set() or (self._latest is not None and self._latest.id > after_id),
                timeout=SCAN_WAIT)
            latest = self._latest
        if self._stop_evt.is_set() or latest is None or latest.id <= after_id:
            return None
        return latest

    # -- main loop -------------------------------------------------------
    def run(self):
        grabber = ScreenGrabber()
        scanner = threading.Thread(target=self._scanner, daemon=True)
        try:
            if winutil.needs_admin_for(self.hwnd):
                self.on_log(t("admin_hint"))
                return
            self.on_log(t("bot_started"))
            if not self._focus():
                self.on_log(t("bot_no_focus"))
            scanner.start()
            last_id = 0
            while not self._stop_evt.is_set():
                if not winutil.is_window_valid(self.hwnd):
                    self.on_log(t("bot_window_closed"))
                    break
                self.on_state(State.SCANNING)
                scan = self._wait_scan(last_id)
                if scan is None:
                    continue
                last_id, self._scale = scan.id, scan.scale
                candidates = self._candidates(scan.dets, scan.shape)
                if not candidates:
                    if self._maybe_roam(grabber, scan.frame, scan.rect):
                        continue
                    self._log_idle()
                    continue
                # A monster here means this is farmable ground: roaming limits are measured from this spot.
                self.roamer.reset_home()
                self._idle_since, self._roam_reason = None, None
                try:
                    # After any outcome the loop simply picks again from the newest scan, which the scanner
                    # kept refreshing during the fight: no scan is waited for.
                    self._engage(grabber, scan.rect, candidates[0])
                finally:
                    self.target_pos = None
        except Exception as exc:  # keep the GUI informed instead of dying silently
            self.on_log(t("bot_error", err=exc))
        finally:
            self._stop_evt.set()
            with self._scan_cond:
                self._scan_cond.notify_all()
            if scanner.is_alive():
                scanner.join(2)
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

    # -- selecting and fighting ----------------------------------------------
    def _engage(self, grabber, rect, target):
        """Click `target` and fight it. Returns the fight's outcome ("stopped" gives up and rescans)."""
        if not self._focus():
            self.on_log(t("bot_retry_focus"))
            self._sleep(1.0)
            return "stopped"
        pos = target.click
        self.on_log(t("bot_target", name=target.name, pos=pos))
        self.target_pos = pos
        self.on_state(State.ATTACKING)
        outcome = "miss"
        for _ in CLICK_HEIGHTS:  # a click that selects nothing is retried at the next height, on the same monster
            x, y = self._click_point(target, CLICK_HEIGHTS[self._height])
            if not inputs.click_at(rect[0] + x, rect[1] + y):
                self.on_log(t("bot_click_rejected"))
                self._sleep(1.0)
                return "stopped"
            outcome = self._fight(grabber, target)
            if outcome != "miss":
                return outcome
            self._height = (self._height + 1) % len(CLICK_HEIGHTS)
        self._mark(pos, 6.0)  # three heights, nothing selected: leave this one alone for a moment
        return outcome

    def _killed(self, target, presses, pos):
        self.kills += 1
        self.on_log(t("bot_killed", name=target.name, n=self.kills, k=presses))
        self._mark(pos, 45.0)  # the corpse keeps its label, right where the monster fell: never click it again
        return "killed"

    def _track(self, target, pos, scan_id):
        """Follow the target's label through the scanner's newest result. Returns (pos, scan_id)."""
        scan = self._latest
        if scan is None or scan.id == scan_id:
            return pos, scan_id
        radius = 110 * scan.scale
        same = [d for d in scan.dets if d.name == target.name and math.dist(d.click, pos) < radius]
        if same:
            pos = min(same, key=lambda d: math.dist(d.click, pos)).click
            self.target_pos = pos
        return pos, scan.id

    def _fight(self, grabber, target):
        """Attack right away; verify while attacking. Returns "killed", "corpse", "miss", "wrong", "timeout" or "stopped"."""
        t0 = time.time()
        pos, scan_id = target.click, 0
        keys = self.cfg.attack_keys
        blind_for = self.cfg.blind_fight_seconds  # blind fights (no readable target window) are time-boxed
        last_press, key_index, first_key = 0.0, 0, True
        panel_seen = alive_seen = noted_missing = False
        dead_since, gone = None, 0
        best_fill, last_progress = 1.0, t0

        while not self._stop_evt.is_set():
            now = time.time()

            # 1) attack: the first key leaves immediately, then the keys rotate
            if keys and now - last_press >= self.cfg.attack_interval:
                key = keys[key_index % len(keys)]
                if self._press(key) and first_key:
                    self.on_log(t("bot_keys_sent", keys=", ".join(keys)))
                    first_key = False
                key_index += 1
                last_press = now

            # 2) keep the label followed (free: the scanner already did the work)
            pos, scan_id = self._track(target, pos, scan_id)

            # 3) look at the target window if it can be read
            panel, frame = None, None
            if self.panel_ok is not False:
                frame, _ = self._grab(grabber)
                panel = read_panel(frame) if frame is not None else None

            if panel is not None and panel.present:
                panel_seen, gone = True, 0
                self.panel_ok, self._panel_misses = True, 0
                if panel.dead:
                    dead_since = dead_since or now
                    if alive_seen:                                  # it was alive and the bar emptied: killed
                        return self._killed(target, key_index, pos)
                    if now - dead_since >= CORPSE_CONFIRM:          # never alive since the click: a corpse
                        self._mark(pos, CORPSE_TTL)
                        self.on_log(t("bot_corpse", name=target.name))
                        return "corpse"
                else:
                    dead_since = None
                    if not alive_seen:
                        alive_seen = True
                        if not self._is_wanted(frame, panel):
                            self._mark(pos, 30.0)
                            return "wrong"
                    if panel.fill < best_fill - 0.02:
                        best_fill, last_progress = panel.fill, now
            elif panel_seen:
                gone += 1                                           # the window vanished: died and was deselected
                if gone >= 2:
                    return self._killed(target, key_index, pos) if alive_seen else "miss"
            else:
                # no target window seen in this fight
                if self.panel_ok is True and now - t0 > SELECT_GRACE:
                    return "miss"                                   # it works on this setup: the click selected nothing
                if self.panel_ok is None and not noted_missing and now - t0 > PANEL_GRACE:
                    noted_missing = True
                    self._panel_misses += 1
                    if frame is not None:
                        self._explain_missing_panel(panel, frame)
                    if self._panel_misses >= PANEL_FAILS_TO_GIVE_UP:
                        self.panel_ok = False
                        self.on_log(t("bot_panel_off"))
                if now - t0 >= blind_for:                           # blind: a fixed, short fight, then on
                    return self._killed(target, key_index, pos)

            if now - t0 > self.cfg.attack_timeout:
                self.on_log(t("bot_timeout"))
                self._mark(pos, 30.0)
                return "timeout"
            if alive_seen and now - last_progress > STALL_SECONDS:
                self.on_log(t("bot_stalled"))
                self._mark(pos, 30.0)
                return "timeout"
            self._sleep(POLL)
        return "stopped"

    def _is_wanted(self, frame, panel):
        """Reject a selection whose name is clearly not one of ours (a player, an NPC, another monster)."""
        text, conf = detect.read_text(frame, panel.name_box)
        names = [detect._norm(m) for m in self.cfg.monsters if m.strip()]
        norm = detect._norm(text)
        if not norm or conf < 0.85 or not names:
            return True  # unsure: do not throw away a real target on a doubtful read
        if max(fuzz.ratio(norm, n) for n in names) >= 55:
            return True
        self.on_log(t("bot_wrong_target", name=text))
        return False

    def _explain_missing_panel(self, panel, frame):
        """Leave evidence when the target window was not seen: the measurements and the frame itself."""
        if frame is None or self._debug_saved >= MAX_DEBUG_FRAMES:
            return
        self._debug_saved += 1
        path = data_path("debug", f"target_window_{self._debug_saved}.png")
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            ok, buf = cv2.imencode(".png", frame)  # imwrite cannot open non-ASCII paths on Windows
            if ok:
                buf.tofile(path)
        except OSError:
            path = "-"
        self.on_log(t("bot_panel_debug", dark=panel.dark, contrast=panel.contrast, text=panel.text, path=path))


def rect_scale(rect):
    return (rect[3] - rect[1]) / detect.REF_HEIGHT
