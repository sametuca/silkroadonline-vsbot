"""Hunt loop on a worker thread.

Selecting a monster is a click on its name label. What happens next is read
from the game's own target window (see target.py):

* empty HP bar right after the click -> that was a corpse (dead monsters keep
  their label): remember the spot and click the next monster of the SAME scan,
  without scanning again;
* filled bar -> attack, watching only that window (milliseconds) until the bar
  empties or the window disappears, then move on at once;
* window unreadable on this game/skin -> fall back to the old behaviour
  (track the name label), so nothing is lost.
"""

import math
import os
import threading
import time
from enum import Enum

import cv2
from rapidfuzz import fuzz

from . import detect, inputs, radar, winutil
from .paths import data_path
from .capture import ScreenGrabber
from .i18n import t
from .roam import PLAYER, Roamer
from .target import Panel, read_panel

POLL = 0.05             # seconds between target-window reads while fighting
SELECT_LAG = 0.12       # the window needs a moment to switch to the newly clicked monster
PANEL_WAIT = 0.35       # how long to wait for the window to appear after a click
MAX_TRIES = 5           # monsters tried from one scan before scanning again
CORPSE_TTL = 120.0      # seconds a corpse's label spot is ignored
ZONE_RADIUS = 45        # px (at 632 px window height) around a remembered spot
STALL_SECONDS = 12.0    # a fight whose target loses no health for this long is abandoned
PANEL_FAILS_TO_GIVE_UP = 3
CLICK_HEIGHTS = (1.0, 0.45, 1.65)  # click offsets below the label, as multiples of the configured one: tried in turn
MAX_DEBUG_FRAMES = 6
LABEL_GONE_SECONDS = 1.5  # label-based mode: the label must be missing this long before the monster counts as dead


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
        self.zones = []          # [(x, y, expires_at)] label spots to ignore: corpses, unreachable monsters
        self.panel_ok = None     # None = not known yet, True = target window readable, False = use name labels
        self._panel_misses = 0
        self._debug_saved = 0
        self._scale = 1.0

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

    # -- main loop -------------------------------------------------------
    def run(self):
        grabber = ScreenGrabber()
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
                if frame is not None:
                    self._scale = rect_scale(rect)
                candidates = self._candidates(dets, frame.shape) if frame is not None else []
                if not candidates:
                    if frame is not None and self._maybe_roam(grabber, frame, rect):
                        continue
                    self._log_idle()
                    self._sleep(self.cfg.scan_interval)
                    continue
                # A monster here means this is farmable ground: roaming limits are measured from this spot.
                self.roamer.reset_home()
                self._idle_since, self._roam_reason = None, None

                for target in candidates[:MAX_TRIES]:
                    if self._stop_evt.is_set():
                        break
                    try:
                        outcome = self._engage(grabber, rect, target)
                    finally:
                        self.target_pos = None
                    if outcome == "done":
                        break  # fought (or gave up): look at the screen again
                    # "next": it was a corpse / not a target: try the next monster from the same scan
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

    # -- selecting and fighting ----------------------------------------------
    def _engage(self, grabber, rect, target):
        """Click `target`, check it with the target window and fight it. Returns "next" or "done"."""
        if not self._focus():
            self.on_log(t("bot_retry_focus"))
            self._sleep(1.0)
            return "done"
        if self.panel_ok is False:  # this game's window is unreadable: the old way
            if not self._confirm(grabber, rect, target):
                return "done"
            self._hunt_by_labels(grabber, rect, target)
            return "done"

        pos = target.click
        self.on_log(t("bot_target", name=target.name, pos=pos))
        self.target_pos = pos
        self.on_state(State.CONFIRMING)

        # Click, then read the target window. A click that misses the sprite selects nothing, so on a
        # missing window try the same monster at other heights below its label before giving up.
        panel, frame = None, None
        for height in CLICK_HEIGHTS:
            x, y = self._click_point(target, height)
            if not inputs.click_at(rect[0] + x, rect[1] + y):
                self.on_log(t("bot_click_rejected"))
                self._sleep(1.0)
                return "done"
            panel, frame = self._wait_panel(grabber)
            if panel.present or self._stop_evt.is_set():
                break

        if not panel.present:
            self._explain_missing_panel(panel, frame)
            self._panel_misses += 1
            if self.panel_ok is True:  # it worked before, so this monster could not be selected
                self._mark(pos, 6.0)
                return "next"
            if self._panel_misses >= PANEL_FAILS_TO_GIVE_UP:
                self.panel_ok = False
                self.on_log(t("bot_panel_off"))
            self._hunt_by_labels(grabber, rect, target, click=False)  # the clicks are done: finish this one the old way
            return "done"
        self._panel_misses = 0
        self.panel_ok = True

        if panel.dead:
            self._mark(pos, CORPSE_TTL)
            self.on_log(t("bot_corpse", name=target.name))
            return "next"
        if not self._is_wanted(frame, panel):
            self._mark(pos, 30.0)
            return "next"
        self._fight(grabber, target, panel)
        return "done"

    def _click_point(self, target, height):
        """Where to click `target`; `height` scales how far below its label (or how low on its body)."""
        x0, y0, w, h = target.box
        if target.source == "model":
            return target.click[0], int(target.click[1] + (height - 1.0) * 0.25 * h)
        return x0 + w // 2, int(y0 + h + self.cfg.click_offset * self._scale * height)

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

    def _wait_panel(self, grabber):
        """Read the target window after a click, tolerating its short lag.

        Right after a click the window may still show the PREVIOUS target (often a corpse),
        so wait a moment, and believe "dead" only when two reads agree.
        """
        self._sleep(SELECT_LAG)
        deadline = time.time() + PANEL_WAIT
        panel, frame = None, None
        while not self._stop_evt.is_set():
            frame, _ = self._grab(grabber)
            if frame is not None:
                panel = read_panel(frame)
                if panel.present:
                    if not panel.dead:
                        return panel, frame
                    self._sleep(POLL * 2)  # a corpse? make sure it is not the old target still on screen
                    frame, _ = self._grab(grabber)
                    again = read_panel(frame) if frame is not None else panel
                    return (again, frame) if again.present else (panel, frame)
            if time.time() >= deadline:
                break
            self._sleep(POLL)
        return panel or Panel(False, 0.0, (0, 0, 0, 0)), frame

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

    def _fight(self, grabber, target, panel):
        """Attack, watching only the target window until the monster dies or the fight stalls."""
        self.on_state(State.ATTACKING)
        started = time.time()
        last_press = 0.0
        last_overlay = started
        last_progress, best_fill = started, panel.fill
        key_index, first_key, gone = 0, True, 0
        while not self._stop_evt.is_set():
            now = time.time()
            if self.cfg.attack_keys and now - last_press >= self.cfg.attack_interval:
                key = self.cfg.attack_keys[key_index % len(self.cfg.attack_keys)]
                if self._press(key) and first_key:
                    self.on_log(t("bot_keys_sent", keys=", ".join(self.cfg.attack_keys)))
                    first_key = False
                key_index += 1
                last_press = now

            frame, _ = self._grab(grabber)
            if frame is not None:
                p = read_panel(frame)
                if p.present and not p.dead:
                    gone = 0
                    if p.fill < best_fill - 0.02:
                        best_fill, last_progress = p.fill, now
                else:
                    gone += 1  # empty bar, or the window vanished (died and was deselected)
                    if p.dead or gone >= 2:
                        self.kills += 1
                        self.on_log(t("bot_killed", name=target.name, n=self.kills, k=key_index))
                        return
                # keep the on-screen markers / recorder fed without scanning every poll
                if now - last_overlay > 1.0 and (self.cfg.overlay or (self.recorder and self.recorder.enabled)):
                    last_overlay = now
                    self._scan(grabber)

            if now - started > self.cfg.attack_timeout:
                self.on_log(t("bot_timeout"))
                self._mark(self.target_pos or target.click, 30.0)
                return
            if now - last_progress > STALL_SECONDS:
                self.on_log(t("bot_stalled"))
                self._mark(self.target_pos or target.click, 30.0)
                return
            self._sleep(POLL)

    # -- the old, label-based way (used when the target window cannot be read) -------
    def _confirm(self, grabber, rect, target):
        """The same label must show up again before we click (filters one-frame OCR noise)."""
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

    def _hunt_by_labels(self, grabber, rect, target, click=True):
        pos = target.click
        if click:
            if not self._focus():
                self.on_log(t("bot_retry_focus"))
                self._sleep(1.0)
                return
            self.on_log(t("bot_target", name=target.name, pos=pos))
            if not inputs.click_at(rect[0] + pos[0], rect[1] + pos[1]):
                self.on_log(t("bot_click_rejected"))
                self._sleep(1.0)
                return

        self.on_state(State.ATTACKING)
        self.target_pos = pos
        radius = 110 * rect_scale(rect)
        started = time.time()
        last_press = 0.0  # press the first attack key right away instead of waiting one interval
        missing_since = None
        key_index = 0
        first_key = True
        while not self._stop_evt.is_set():
            now = time.time()
            if now - last_press >= self.cfg.attack_interval and self.cfg.attack_keys:
                key = self.cfg.attack_keys[key_index % len(self.cfg.attack_keys)]
                if self._press(key) and first_key:
                    self.on_log(t("bot_keys_sent", keys=", ".join(self.cfg.attack_keys)))
                    first_key = False
                key_index += 1
                last_press = now
            _, _, dets = self._scan(grabber)
            same = [d for d in dets if d.name == target.name and math.dist(d.click, pos) < radius]
            if same:
                missing_since = None
                pos = min(same, key=lambda d: math.dist(d.click, pos)).click
                self.target_pos = pos
            else:
                # An OCR miss or a monster running past the search radius must not count as a death:
                # the label has to stay gone for a while.
                missing_since = missing_since or now
                if now - missing_since >= LABEL_GONE_SECONDS:
                    self.kills += 1
                    self.on_log(t("bot_killed", name=target.name, n=self.kills, k=key_index))
                    return
            if now - started > self.cfg.attack_timeout:
                self.on_log(t("bot_timeout"))
                self._mark(pos, 30.0)
                return
            self._sleep(self.cfg.scan_interval)

def rect_scale(rect):
    return (rect[3] - rect[1]) / detect.REF_HEIGHT

