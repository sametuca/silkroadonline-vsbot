# Silkroad Vision Bot

**Screen-vision auto-hunt bot for Silkroad Online private servers — no memory reading, no packet injection.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows-blue)]()

This is a ground-up redesign (v2), not a refactor of the old single-file
script. It only ever looks at pixels already rendered to your screen and
sends synthetic keyboard/mouse input — the same information and the same
actions a player has. It never opens a handle to the game process and
never touches the network connection, so it doesn't collide with
anti-cheat systems that watch process memory or the wire protocol.

## 🎮 Just want to run it? (no Python needed)

1. Go to [**Releases**](../../releases/latest) and download `SilkroadVisionBot.exe`.
2. Double-click it. That's it — no installer, no `pip`, no GitHub account.
3. If Windows SmartScreen warns about an "unrecognized app" (normal for a
   small unsigned tool), click **More info → Run anyway**.
4. If skill keys don't seem to register in-game, right-click the exe →
   **Run as administrator**.

The exe is rebuilt automatically from this repo's source on every release
(see the `Actions` tab), so it's always the same code you can read here —
nothing hidden is added during packaging.

## Design decisions (and why)

A straight "one PNG template, `cv2.matchTemplate`, done" bot is fragile:
lighting, zoom and monster animation all break a raw pixel match, and
scanning a whole viewport with template matching every frame is slow.
This version is built as a **layered pipeline** instead:

| Layer | What | Why |
|---|---|---|
| **Fast capture** | [`mss`](https://github.com/BoboTiG/python-mss) instead of `PIL.ImageGrab` | Low-level OS capture, no GDI round-trip — a tighter loop without burning CPU on screenshots. |
| **Color candidates** | HSV mask → connected components (`vsbot/color_detect.py`) | Name-plates are flat, saturated colors regardless of the 3D scene behind them. Finding *candidates* this way is cheap and survives zoom/lighting changes; you calibrate the color once by clicking on a name in-game. |
| **Shape confirm** | Multi-scale **edge** template matching (Canny + `matchTemplate`), run only on the small crops around each candidate | Edges instead of raw grayscale tolerate lighting differences; multiple scales tolerate camera zoom drift. Only matching small crops (not the whole region) is what makes this fast enough to run every frame. |
| **Optional OCR** | `easyocr` + fuzzy match (`rapidfuzz`), pluggable | Reads the *actual name* instead of comparing pixels — most precise option, but a ~500MB ML dependency, so it's opt-in, not required. |
| **Death detection** | HP-bar fill-ratio reading (`color_detect.read_hp_ratio`), falls back to a timer-based reclick guard if no HP bar is calibrated | A measurement beats a guess: reading the actual health bar tells you precisely when a kill lands instead of assuming after N seconds. |
| **Architecture** | Explicit state machine (`vsbot/state_machine.py`): `SCANNING → CONFIRMING → ATTACKING → AWAITING_DEATH → LOOTING` | Each phase is isolated and logged, instead of one long function guessing what to do next. |
| **Config** | JSON multi-profile store (`vsbot/profiles.py`) | Different characters/farm spots need different regions, keys and thresholds — save/load named presets instead of re-entering everything. |

None of this needs a network capture, a memory scanner, or DLL injection —
it's all standard image processing (OpenCV) plus Windows' public
`SendInput` API for keyboard/mouse.

## Running from source (developers)

- Windows 10/11, Python 3.9+
- Game running in **windowed mode** (not fullscreen)

```bash
pip install -r requirements.txt
python main.py
```

Optional, for the OCR detection mode: `pip install easyocr` (large
download, CPU-only is fine). Without it, OCR mode is simply unavailable
and the GUI tells you so — everything else works normally.

Run as Administrator (right-click `run_gui.bat`) if key presses don't
register in-game.

**Building the .exe yourself:** `.\build.ps1` (or the same command the CI
runs — see `.github/workflows/build-release.yml`) produces
`dist\SilkroadVisionBot.exe`. Every push to `main` also builds one
automatically as a downloadable Actions artifact; pushing a `vX.Y.Z` tag
additionally attaches it to a GitHub Release.

## Project layout

```
silkroadonline-vsbot/
├── main.py                  # entry point
├── vsbot/
│   ├── paths.py               # resolves data dir: project root when run from source, exe's folder when frozen
│   ├── i18n.py               # TR/EN strings, language.json persistence
│   ├── winutil.py            # DPI awareness, window listing, one-off screenshots
│   ├── capture.py            # mss-based fast capture for the hunt loop
│   ├── color_detect.py       # HSV candidate scan + HP-bar reader + eyedropper
│   ├── detection.py          # multi-scale edge template matching + hybrid/OCR modes
│   ├── ocr.py                # optional easyocr + rapidfuzz layer
│   ├── input_methods.py      # SendInput / pydirectinput / keyboard backends
│   ├── state_machine.py      # hunt-loop State enum
│   ├── bot_engine.py         # the state machine itself (background thread)
│   ├── profiles.py           # JSON multi-profile save/load
│   ├── gui.py                 # Tkinter UI
│   └── region_select.py      # click-drag region / single-point screen picker
├── monsters/                 # your PNG monster templates (for template/hybrid modes)
├── profiles/                  # saved settings presets (git-ignored, per-user)
├── assets/                    # icons/logo used by the GUI
├── build.ps1                  # builds dist\SilkroadVisionBot.exe locally
├── .github/workflows/build-release.yml  # CI: builds the exe, attaches to Releases on tag push
└── requirements.txt
```

## Using it

1. **Set Hunt Region** — drag a box over the area of the screen where
   monsters/name-plates appear.
2. **Calibrate Nameplate Color** — click once directly on a monster's
   name text; the bot derives an HSV range from that pixel. This powers
   every detection mode except plain OCR.
3. Pick a **Detection Mode**:
   - **Hybrid** (default) — color candidates confirmed by template shape.
     Best balance of speed and accuracy for most people.
   - **Color only** — no templates needed at all, just the calibrated
     color. Fastest, least precise if multiple things share that color.
   - **Template only** — full-frame template search, no color
     pre-filter. Slower, useful if your nameplate color isn't distinct.
   - **OCR** — reads the actual name (requires `easyocr`).
4. (Hybrid/Template modes) **Add Template** — drag a box around a
   monster's name/body, give it a name; saved as a PNG in `monsters/`.
5. Optionally set **HP Bar Region** by dragging over the target's health
   bar — enables precise death detection instead of a timer guess.
6. Set **Skill Keys**, intervals, optional **Loot Key**, pick an
   **Input Method** (Auto is fine for most setups), then **Start**.
7. Press **Q** anywhere (or the Stop button) to stop.
8. **Save** your setup as a named profile so you don't have to redo this
   for a different character or farm spot.

**Keypress Only Mode** skips detection entirely and just presses your
skill keys on a timer. **Buffs** run on their own independent timer.

## License

MIT — see [LICENSE](LICENSE). Educational use; you are responsible for
complying with the terms of service of whatever server you run this
against, and for any consequences of using automation tools.
