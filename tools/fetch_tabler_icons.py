"""Download Tabler Icons (MIT) PNGs from unpkg for the GUI. Run after clone if icons missing."""
import os
import urllib.request

# https://tabler.io/icons — @tabler/icons-png
BASE = "https://unpkg.com/@tabler/icons-png@3.36.1/icons/outline/"
# (remote_filename, local_filename)
ICONS = [
    ("player-play.png", "start.png"),
    ("player-stop.png", "stop.png"),
    ("app-window.png", "window.png"),
    ("crosshair.png", "region.png"),
    ("photo-plus.png", "template.png"),
    ("file-text.png", "log.png"),
    ("layout-dashboard.png", "status.png"),
    ("refresh.png", "refresh.png"),
    ("check.png", "ok.png"),
    ("x.png", "cancel.png"),
    ("device-floppy.png", "save.png"),
]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "icons")


def main():
    os.makedirs(OUT, exist_ok=True)
    for remote, local in ICONS:
        url = BASE + remote
        dest = os.path.join(OUT, local)
        with urllib.request.urlopen(url, timeout=45) as r:
            data = r.read()
        with open(dest, "wb") as f:
            f.write(data)
        print("ok", local, len(data), "bytes")


if __name__ == "__main__":
    main()
