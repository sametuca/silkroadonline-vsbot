<div align="center">

# Silkroad Vision Bot

### [🇬🇧 English](README.md) &nbsp;|&nbsp; [🇹🇷 Türkçe](README.tr.md)

Screen-vision auto-hunt bot for Silkroad-style MMOs. It reads monster **name labels** off the screen,
picks targets, attacks, loots, and walks around to find more.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows-blue)]()

</div>

No memory reading, no packet injection, no DLL injection. The bot only looks at pixels already on your screen and
sends the same keyboard and mouse input a player would.

## Quick start

1. Download `SilkroadVisionBot.exe` from [**Releases**](../../releases/latest) and double-click it (no Python needed).
   Or from source: `pip install -r requirements.txt`, then `python main.py`.
2. Run the game in **windowed mode** and keep its window uncovered. The game window is picked automatically.
3. Enter your attack key (e.g. `1`) and, optionally, a loot key.
4. Press **START** (or **F9**).

The first time, the bot looks at the screen and asks:
*"I found Mangyang (5 on screen). Should I hit these?"* Click **Yes** and the hunt begins.

You never type a monster list. Normal, champion and giant monsters share the same name, so a single target covers
all of them. The target is saved: next time just press START. To switch monsters, press **Search again**.
Your own character name is read from the window title (`[YourName] ...`) and ignored automatically. If other names
show up (players, NPCs), only the most frequent group is ticked by default.

**Test scan** shows what the bot recognises (green boxes) without attacking anything.

### Roaming

When no target monster is on screen for a few seconds, the character **walks to a nearby ground point** and looks
again, changing direction every few steps. Turn it off with the **"Search by roaming when no monster"** switch.

> The roaming walk has no map boundary yet, so over a long time it can drift away from your starting area.

### Administrator rights (important)

If the game runs **as administrator** and this program does not, Windows (UIPI) **silently drops** every key and click
the bot sends: it sees monsters but nothing happens. The program detects this, shows a warning in the sidebar and
offers a **Restart as administrator** button.

### Windows warnings

The exe is unsigned, so SmartScreen may show "Unknown publisher": click **More info → Run anyway**. Like any program
that sends keys and reads the screen, some antivirus tools may flag it by mistake. All source code is in this repository;
you can build the exe yourself with `.\build.ps1`.

## How it works

1. White, thin, outlined text blobs are found on screen (fixed UI such as HUD, minimap and chat is excluded).
2. Each blob is read with [RapidOCR](https://github.com/RapidAI/RapidOCR) (ONNX, no separate install).
3. The text is fuzzy-matched against your target (`Mangyang` ≈ `Mangyan9`).
4. The nearest match is clicked just below its label and the attack keys are pressed.
5. When the label disappears for a few scans the monster counts as dead, the loot key is pressed and the loop restarts.

States: `Searching → Confirming → Attacking → Looting`, plus `Roaming` when nothing is on screen.

## Optional: train a YOLO model

OCR works out of the box. A trained detector can see the monster sprite itself, which helps when labels are hidden.
It needs real data, so it is an optional upgrade.

1. Under **Advanced**, press **Collect training data** and play or hunt as usual. Boxes are labelled automatically
   from the name labels, with no hand drawing. Output goes to `dataset/` in YOLO format.
2. Collect a few hundred frames per monster with varied angles, distances and lighting.
3. Once: `pip install -r requirements-train.txt` (training only; it pulls in torch).
4. Press **Train model** (or `python -m srbot.train`). On CPU this takes minutes.
5. `models/monsters.onnx` appears and **Detector: Automatic** uses it, falling back to OCR when no model exists.
   Inference needs only `onnxruntime` (about 40 ms per frame), so the exe stays small.

Recording relies on OCR labels, so collect data while the detector is on **OCR** (not on model-only mode).

## Development

```bash
pip install -r requirements.txt pytest
pytest                                       # unit tests (OCR detection, recorder, YOLO decoding, hunt loop, roaming)
.\build.ps1                                  # builds dist\SilkroadVisionBot.exe and smoke-tests it
SilkroadVisionBot.exe --selftest result.txt  # verifies OCR/onnxruntime inside the built exe
```

Settings live in `config.json` (git-ignored). On every push to `main`, GitHub Actions runs the tests, builds the exe,
verifies it with `--selftest` and updates the "latest" [release](../../releases/latest).
Training dependencies are deliberately left out of the exe, which is why it is about 100 MB.

## About

**Silkroad Vision Bot** v3 is developed by **Samet Uca**.

- GitHub: [github.com/sametuca](https://github.com/sametuca)
- Email: [sametuca@hotmail.com](mailto:sametuca@hotmail.com)
- Project: [github.com/sametuca/silkroadonline-vsbot](https://github.com/sametuca/silkroadonline-vsbot)

Bug reports and ideas are welcome via [Issues](../../issues).

Using bots may violate a game server's rules. You are responsible for how you use this software.

## License

[MIT](LICENSE)
