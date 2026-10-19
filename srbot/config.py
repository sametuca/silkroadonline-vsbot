"""Single JSON settings file with sane defaults - nothing to calibrate."""

import json
from dataclasses import asdict, dataclass, field, fields

from .paths import data_path

CONFIG_FILE = data_path("config.json")

# Screen areas that never contain monster name labels, as fractions of the
# game window (left, top, right, bottom): top-left HUD, minimap, chat,
# bottom skill bar, right-side quick buttons.
DEFAULT_EXCLUDES = [
    (0.00, 0.00, 0.40, 0.17),
    (0.82, 0.00, 1.00, 0.32),
    (0.00, 0.66, 0.85, 0.88),
    (0.00, 0.88, 1.00, 1.00),
    (0.70, 0.32, 1.00, 0.60),
]


@dataclass
class Config:
    language: str = ""              # "tr" | "en"; empty = ask on first start
    window_title: str = ""
    monsters: list = field(default_factory=list)
    player_name: str = ""
    attack_keys: list = field(default_factory=lambda: ["1", "2", "3", "4"])
    attack_interval: float = 0.6
    scan_interval: float = 0.12
    click_offset: int = 18          # px below the name label, at 632px window height
    match_threshold: int = 78       # fuzzy name match, 0-100
    blind_fight_seconds: float = 1.2  # without a readable target window: attack this long, then move on
    overlay: bool = True            # draw boxes over the monsters on the game window
    roam: bool = True               # walk around when no target monster is on screen
    roam_after: float = 2.5         # seconds without a target before walking
    roam_step: int = 360            # walk distance in px at 632px window height
    roam_radius: float = 4.0        # farming-area radius around the start spot, in steps
    roam_wait: float = 1.3          # seconds to let the character walk before the next step
    detector: str = "auto"          # auto (model if trained, else OCR) | ocr | model
    model_conf: float = 0.4
    attack_timeout: float = 30.0
    excludes: list = field(default_factory=lambda: [list(r) for r in DEFAULT_EXCLUDES])

    def save(self, path=CONFIG_FILE):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path=CONFIG_FILE):
        cfg = cls()
        try:
            with open(path, encoding="utf-8") as f:
                raw = json.load(f)
        except (OSError, ValueError):
            return cfg
        for fld in fields(cls):
            if fld.name in raw:
                setattr(cfg, fld.name, raw[fld.name])
        return cfg
