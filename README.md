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
2. Run the game in **windowed mode** and keep its window uncovered.
3. Follow the three start-up steps (prefilled from your last run):
   1. **Game**: pick the game window.
   2. **Monster**: type the monster's name **exactly as shown above it in the game** (case does not matter; separate
      several monsters with commas). Not sure about the spelling? **Read the name from the screen** shows what the
      bot sees and lets you tick it.
   3. **Keys**: your attack key(s) (e.g. `1,2,3`), an optional loot key, and the roaming switch.
4. Press **START** (or **F9**).

Normal, champion and giant monsters share the same name, so one name covers all of them. Your own character name is
read from the window title (`[YourName] ...`) and ignored automatically. **Change settings** on the dashboard reopens the steps.

**Test scan** reports in the log how many target monsters the bot sees on screen, without attacking anything.

### Roaming

When no target monster is on screen for a few seconds, the bot looks at the **radar** (minimap in the top-right
corner) instead of walking at random:

- It walks toward the **nearest red dot** (a monster), so the search continues where monsters actually are.
- It stays inside the **farming area**: dots farther than the area radius from the spot where the bot last saw a
  monster are ignored (set the radius in step 3, 2 to 12 steps).
- If the radar shows nothing, it walks back to the farming area and only searches with short steps around it.
- It learns how the radar is oriented (rotating with the camera or fixed north) by watching how the dots move after
  each step, so it works with any camera angle.

Turn roaming off with the **"Search by roaming when no monster"** switch.

> The radar is expected in the top-right corner of the game window at its default size. The walk position is
> dead-reckoned from the clicks, so it is approximate rather than exact.

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
