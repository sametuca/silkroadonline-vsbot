import os

from PIL import Image

from srbot import theme
from srbot.paths import resource_path


def test_icon_assets_exist_and_are_usable():
    for name in ("logo.png", "app_icon.png", "icon.ico"):
        assert os.path.isfile(resource_path("assets", name)), name
    ico = Image.open(resource_path("assets", "icon.ico"))
    assert (256, 256) in ico.info["sizes"] and (16, 16) in ico.info["sizes"]
    tile = Image.open(resource_path("assets", "app_icon.png"))
    assert tile.size == (512, 512) and tile.mode == "RGBA"
    assert tile.getpixel((0, 0))[3] == 0          # rounded corners are transparent
    assert tile.getpixel((256, 256))[3] == 255    # the tile itself is opaque


def test_palette_is_valid_hex():
    for name in ("BG", "CARD", "FIELD", "INSET", "ACCENT", "SUCCESS", "DANGER", "PINK", "TEXT", "MUTED"):
        value = getattr(theme, name)
        assert len(value) == 7 and value.startswith("#") and int(value[1:], 16) >= 0, name
