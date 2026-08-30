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

from . import color_detect, detection, input_methods, ocr
from .capture import ScreenGrabber
from .detection import ReclickGuard
from .state_machine import State

HSVRange = Tuple[Tuple[int, int, int], Tuple[int, int, int]]


@dataclass
class BotConfig:
    hunt_region: Optional[tuple] = None  # (left, top, right, bottom) absolute screen coords
    monsters_dir: str = "monsters"

    detection_mode: str = "hybrid"  # "hybrid" | "color" | "template" | "ocr"
    nameplate_hsv: HSVRange = field(default_factory=lambda: color_detect.DEFAULT_NAMEPLATE_HSV)
    template_threshold: float = 0.40
    target_monsters: List[str] = field(default_factory=list)  # lowercase, empty = any

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
        self.state = State.SCANNING
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
            time.sleep(cfg.mob_interval)
            return

        left, top, _r, _b = cfg.hunt_region
        screen_x, screen_y = left + found.center_x, top + found.center_y

        if cfg.hp_bar_rect is None and self.reclick_guard.is_recent(found.template_name, screen_x, screen_y, now):
            time.sleep(cfg.mob_interval)
            return

        self.log(f"🎯 {found.template_name} (confidence={found.confidence:.2f})")
        input_methods.click_at(screen_x, screen_y, cfg.input_method)
        self._current_target = found
        self._current_target_screen_xy = (screen_x, screen_y)

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
        if self.config.hp_bar_rect is not None:
            self._attack_started_at = self._attack_started_at or now
            self.state = State.AWAITING_DEATH
        else:
            # no HP bar calibrated: one attack burst per acquisition, then
            # treat as dead and move on (ReclickGuard already remembers it)
            self.kills += 1
            self.state = State.LOOTING
        time.sleep(self.config.mob_interval)

    def _do_await_death(self, now):
        ratio = self._read_hp_ratio()
        timed_out = (now - self._attack_started_at) >= self.config.max_attack_seconds

        if ratio is None or ratio <= self.config.hp_dead_threshold or timed_out:
            if timed_out:
                self.log("⏱ Attack timed out, moving on")
            self.kills += 1
            self.state = State.LOOTING
            return

        self._press_skills()
        time.sleep(self.config.mob_interval)

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
        return detection.detect_hybrid(scene, self.templates, cfg.nameplate_hsv, cfg.template_threshold, target_names)

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
