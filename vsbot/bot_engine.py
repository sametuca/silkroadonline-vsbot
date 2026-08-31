"""The hunt loop, running on a background thread as an explicit state machine.

SCANNING -> (found + clicked) -> CONFIRMING -> ATTACKING -> AWAITING_DEATH
    -> LOOTING -> back to SCANNING

Buffs and Auto-TAB are checked every tick regardless of state (they're
timers, not part of the hunt sequence). If no HP-bar region has been
calibrated, AWAITING_DEATH degrades gracefully to "press skills once per
acquisition, assume it died, let ReclickGuard stop us from re-clicking a
corpse".
"""

import threading
import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple

from . import color_detect, detection, input_methods, ocr, winutil
from .capture import ScreenGrabber
from .detection import ReclickGuard
from .state_machine import State

HSVRange = Tuple[Tuple[int, int, int], Tuple[int, int, int]]


@dataclass
class BotConfig:
    hunt_region: Optional[tuple] = None  # (left, top, right, bottom) absolute screen coords
    game_hwnd: Optional[int] = None  # kept focused every cycle - SendInput only reaches the foreground window
    monsters_dir: str = "monsters"

    detection_mode: str = "color"  # "hybrid" | "color" | "template" | "ocr"
    nameplate_hsv: HSVRange = field(default_factory=lambda: color_detect.DEFAULT_NAMEPLATE_HSV)
    template_threshold: float = 0.40
    target_monsters: List[str] = field(default_factory=list)  # lowercase, empty = any
    # Folds OCR into the default (hybrid) pipeline automatically when a fast
    # engine (Tesseract) happens to be installed - reads the winning
    # candidate's text once per cycle to veto an obvious false positive. A
    # no-op with no OCR engine installed, so it's safe to leave on.
    ocr_confirm: bool = True

    keypress_only: bool = False
    auto_tab: bool = False
    auto_tab_interval: float = 3.0

    skill_keys: List[str] = field(default_factory=lambda: ["1", "2", "3", "4"])
    skill_interval: float = 0.15
    mob_interval: float = 0.2
    reclick_lockout: float = 2.5

    # HP-bar based death confirmation (optional - more reliable than a timer
    # when calibrated). hp_bar_rect is relative to hunt_region's top-left.
    hp_bar_rect: Optional[tuple] = None  # (x, y, w, h)
    hp_bar_filled_hsv: HSVRange = ((40, 70, 70), (85, 255, 255))  # default: greenish fill
    hp_dead_threshold: float = 0.05
    max_attack_seconds: float = 20.0  # safety valve if the HP bar never reads as empty

    loot_key: Optional[str] = None
    loot_wait: float = 0.4

    input_method: str = "auto"

    buffs_enabled: bool = False
    buff_keys: List[str] = field(default_factory=list)
    buff_interval: float = 60.0


class BotEngine:
    def __init__(self, config: BotConfig, log_fn: Callable[[str], None] = print):
        self.config = config
        self.log = log_fn
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.running = False
        self.kills = 0
        self.start_time = 0.0
        self.state = State.SCANNING
        self.reclick_guard = ReclickGuard(config.reclick_lockout)
        self.templates = []
        self._grabber: Optional[ScreenGrabber] = None
        self._last_buff_time = 0.0
        self._last_auto_tab_time = 0.0
        self._current_target: Optional[detection.Detection] = None
        self._current_target_screen_xy = (0, 0)
        self._attack_started_at = 0.0
        self._pending_detection = None  # (name, screen_x, screen_y) seen last scan, awaiting a 2nd-frame match
        self._death_miss_count = 0  # consecutive scans where the target's name-plate wasn't found
        self._focus_warning_logged = False
        self._scan_count = 0
        self._last_heartbeat_at = 0.0

    # -- lifecycle -----------------------------------------------------
    def start(self):
        if self.running:
            return
        self.templates = detection.load_monster_templates(self.config.monsters_dir)
        if self.config.detection_mode == "template" and not self.config.keypress_only and not self.templates:
            self.log("⚠ No monster templates loaded.")
        if self.config.detection_mode == "ocr" and not ocr.is_available():
            self.log("⚠ OCR mode selected but easyocr isn't installed - falling back to 'hybrid'.")
            self.config.detection_mode = "hybrid"

        self.reclick_guard.set_lockout(self.config.reclick_lockout)
        self.kills = 0
        self.start_time = time.time()
        self._last_buff_time = self.start_time
        self._last_auto_tab_time = self.start_time
        self._pending_detection = None
        self._death_miss_count = 0
        self._focus_warning_logged = False
        self._scan_count = 0
        self._last_heartbeat_at = self.start_time
        self.state = State.SCANNING

        if self.config.game_hwnd is not None and not winutil.is_foreground(self.config.game_hwnd):
            winutil.bring_window_to_front(self.config.game_hwnd)
        if not winutil.is_admin():
            self.log("ℹ️ Yönetici modunda çalışmıyorsunuz. Oyun yönetici olarak açıksa "
                      "(çoğu anti-cheat bunu gerektirir) tuşlar/tıklamalar oyuna ulaşmaz - "
                      "bu durumda botu da yönetici olarak çalıştırın.")
        self._stop_event.clear()
        self.running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self.running = False

    def elapsed_seconds(self):
        return time.time() - self.start_time if self.start_time else 0.0

    # -- main loop -------------------------------------------------------
    def _run(self):
        self._grabber = ScreenGrabber()
        try:
            while not self._stop_event.is_set():
                self._tick()
        except Exception as exc:
            self.log(f"❌ Bot loop error: {exc}")
        finally:
            if self._grabber is not None:
                self._grabber.close()
            self.running = False

    # -- per-cycle dispatch -----------------------------------------------
    def _tick(self):
        now = time.time()
        cfg = self.config

        self._ensure_game_focused()

        if cfg.buffs_enabled and cfg.buff_keys and now - self._last_buff_time >= cfg.buff_interval:
            self._cast_buffs()
            self._last_buff_time = now

        if cfg.keypress_only:
            self._press_skills()
            time.sleep(cfg.mob_interval)
            return

        if self.state == State.SCANNING:
            self._do_scan(now)
        elif self.state == State.CONFIRMING:
            self._do_confirm()
        elif self.state == State.ATTACKING:
            self._do_attack(now)
        elif self.state == State.AWAITING_DEATH:
            self._do_await_death(now)
        elif self.state == State.LOOTING:
            self._do_loot()

    # -- states -------------------------------------------------------------
    def _do_scan(self, now):
        cfg = self.config
        self._scan_count += 1
        if now - self._last_heartbeat_at >= 8.0:
            self._last_heartbeat_at = now
            self.log(f"🔍 Taranıyor (#{self._scan_count}, mod={cfg.detection_mode}) - "
                     f"henüz hedef bulunamadı" if self.kills == 0 else f"🔍 Taranıyor (#{self._scan_count})")

        if cfg.auto_tab and now - self._last_auto_tab_time >= cfg.auto_tab_interval:
            input_methods.press_key("tab", cfg.input_method)
            self._last_auto_tab_time = now
            time.sleep(0.15)

        scene = self._capture()
        if scene is None:
            time.sleep(cfg.mob_interval)
            return

        target_names = set(cfg.target_monsters) if cfg.target_monsters else None
        found = self._run_detection(scene, target_names)
        if found is None:
            self._pending_detection = None
            time.sleep(cfg.mob_interval)
            return

        left, top, _r, _b = cfg.hunt_region
        screen_x, screen_y = left + found.center_x, top + found.center_y

        if cfg.hp_bar_rect is None and self.reclick_guard.is_recent(found.template_name, screen_x, screen_y, now):
            self._pending_detection = None
            time.sleep(cfg.mob_interval)
            return

        # Require the same detection twice in a row before committing to a
        # click - filters single-frame noise, but only worth the latency
        # for hybrid/template modes where a false click could mean the
        # wrong monster species. In color mode there's no "species" to get
        # wrong, and a real target's box jitters a few pixels frame to
        # frame (walk animation, camera drift) - requiring it to land
        # within a tight tolerance twice in a row was rejecting almost
        # every real detection, not just noise (this was the main cause of
        # very sparse clicking). So: color mode trusts the first hit.
        if cfg.detection_mode != "color":
            pending = self._pending_detection
            matches_pending = (
                pending is not None and pending[0] == found.template_name
                and abs(pending[1] - screen_x) <= 30 and abs(pending[2] - screen_y) <= 30
            )
            if not matches_pending:
                self._pending_detection = (found.template_name, screen_x, screen_y)
                time.sleep(0.08)
                return
        self._pending_detection = None

        self.log(f"🎯 {found.template_name} (confidence={found.confidence:.2f})")
        input_methods.click_at(screen_x, screen_y, cfg.input_method)
        self._current_target = found
        self._current_target_screen_xy = (screen_x, screen_y)
        self._death_miss_count = 0

        if cfg.hp_bar_rect is not None:
            self.state = State.CONFIRMING
        else:
            self.reclick_guard.remember(found.template_name, screen_x, screen_y, now)
            self._attack_started_at = now
            self.state = State.ATTACKING

    def _do_confirm(self):
        time.sleep(0.25)
        ratio = self._read_hp_ratio()
        if ratio is not None and ratio > self.config.hp_dead_threshold:
            self._attack_started_at = time.time()
            self.state = State.ATTACKING
        else:
            # click missed / no valid target selected - try again
            self.state = State.SCANNING

    def _do_attack(self, now):
        self._press_skills()
        self._attack_started_at = self._attack_started_at or now
        self.state = State.AWAITING_DEATH
        time.sleep(self.config.mob_interval)

    def _do_await_death(self, now):
        cfg = self.config
        timed_out = (now - self._attack_started_at) >= cfg.max_attack_seconds

        if cfg.hp_bar_rect is not None:
            ratio = self._read_hp_ratio()
            is_dead = ratio is None or ratio <= cfg.hp_dead_threshold
        else:
            # No HP bar calibrated: infer death from the name-plate actually
            # disappearing from where we last saw it (2 consecutive misses,
            # so one occluded/flickered frame doesn't end the fight early) -
            # a measurement, not the old "attack once and assume dead" guess.
            is_dead = self._nameplate_gone()

        if is_dead or timed_out:
            if timed_out:
                self.log("⏱ Attack timed out, moving on")
            self.kills += 1
            self.state = State.LOOTING
            return

        self._press_skills()
        time.sleep(cfg.mob_interval)

    def _nameplate_gone(self):
        scene = self._capture()
        if scene is None:
            return False  # a capture hiccup shouldn't end the fight early

        name = self._current_target.template_name if self._current_target else None
        target_names = {name.lower()} if name else None
        found = self._run_detection(scene, target_names)

        still_there = False
        if found is not None:
            left, top, _r, _b = self.config.hunt_region
            fx, fy = left + found.center_x, top + found.center_y
            tx, ty = self._current_target_screen_xy
            still_there = abs(fx - tx) <= 30 and abs(fy - ty) <= 30

        if still_there:
            self._death_miss_count = 0
            return False

        self._death_miss_count += 1
        return self._death_miss_count >= 2

    def _do_loot(self):
        if self.config.loot_key:
            input_methods.press_key(self.config.loot_key, self.config.input_method)
        time.sleep(self.config.loot_wait)
        self._current_target = None
        self.state = State.SCANNING

    # -- helpers -------------------------------------------------------
    def _run_detection(self, scene, target_names):
        cfg = self.config
        mode = cfg.detection_mode
        if mode == "color":
            return detection.detect_color_only(scene, cfg.nameplate_hsv, target_names)
        if mode == "template":
            return detection.detect_template(scene, self.templates, cfg.template_threshold, target_names)
        if mode == "ocr":
            return detection.detect_with_ocr(scene, cfg.nameplate_hsv, target_names)

        found = detection.detect_hybrid(scene, self.templates, cfg.nameplate_hsv, cfg.template_threshold,
                                         target_names)
        if found is not None and cfg.ocr_confirm and not detection.confirm_with_ocr(scene, found, target_names):
            self.log(f"🔎 OCR discarded a likely false positive ({found.template_name})")
            return None
        return found

    def _read_hp_ratio(self):
        cfg = self.config
        if cfg.hp_bar_rect is None:
            return None
        scene = self._capture()
        if scene is None:
            return None
        return color_detect.read_hp_ratio(scene, cfg.hp_bar_rect, cfg.hp_bar_filled_hsv)

    def _press_skills(self):
        for key in self.config.skill_keys:
            if self._stop_event.is_set():
                return
            input_methods.press_key(key, self.config.input_method)
            time.sleep(self.config.skill_interval)

    def _ensure_game_focused(self):
        """Refocus the game window if the user clicked away from it.

        SendInput has no concept of a "target window" - it goes wherever
        Windows currently has focus. Without this, clicking into a text
        editor (or anything else) mid-run silently redirects every
        subsequent key press there instead of the game.
        """
        hwnd = self.config.game_hwnd
        if hwnd is None or not winutil.is_window_valid(hwnd):
            return
        if winutil.is_foreground(hwnd):
            return

        got_focus = winutil.bring_window_to_front(hwnd)
        time.sleep(0.05)
        if not got_focus and not self._focus_warning_logged:
            self._focus_warning_logged = True
            admin_hint = "" if winutil.is_admin() else " Botu YÖNETİCİ olarak çalıştırmayı deneyin."
            self.log("⚠ Oyun penceresi öne getirilemedi - girdiler oyuna ulaşmayabilir."
                      " Oyun yönetici modunda çalışıyor olabilir." + admin_hint)

    def _cast_buffs(self):
        self.log("✨ Casting buffs")
        for key in self.config.buff_keys:
            if self._stop_event.is_set():
                return
            input_methods.press_key(key, self.config.input_method)
            time.sleep(self.config.skill_interval)

    def _capture(self):
        if self._grabber is None or self.config.hunt_region is None:
            return None
        try:
            return self._grabber.grab_bgr(self.config.hunt_region)
        except Exception as exc:
            self.log(f"❌ Screen capture failed: {exc}")
            return None
