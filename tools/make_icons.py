"""Builds the app icons from the transparent logo in assets/logo.png.

    python tools/make_icons.py

Writes assets/app_icon.png (iOS-style rounded square on a dark gradient) and
assets/icon.ico (16-256 px, used for the exe and the window). Committed
outputs; rerun only when the logo changes.
"""

from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ASSETS = Path(__file__).resolve().parent.parent / "assets"
SIZE = 1024
RADIUS = 0.2237          # Apple's icon corner radius as a fraction of the side
GLYPH_SCALE = 0.70


def gradient(size, top, bottom):
    """Vertical gradient with a faint diagonal tint, so the tile does not look flat."""
    base = Image.new("RGB", (1, size))
    for y in range(size):
        k = y / (size - 1)
        base.putpixel((0, y), tuple(round(top[i] + (bottom[i] - top[i]) * k) for i in range(3)))
    return base.resize((size, size))


def rounded_mask(size, radius_fraction, supersample=4):
    big = size * supersample
    mask = Image.new("L", (big, big), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, big - 1, big - 1), radius=int(big * radius_fraction), fill=255)
    return mask.resize((size, size), Image.LANCZOS)


def main():
    logo = Image.open(ASSETS / "logo.png").convert("RGBA")
    tile = gradient(SIZE, (44, 44, 56), (20, 20, 26)).convert("RGBA")

    glyph_size = int(SIZE * GLYPH_SCALE)
    glyph = logo.resize((glyph_size, glyph_size), Image.LANCZOS)
    # soft glow under the glyph: the pink/blue lines stay readable on the dark tile
    glow = glyph.filter(ImageFilter.GaussianBlur(SIZE * 0.025))
    glow.putalpha(glow.getchannel("A").point(lambda a: int(a * 0.55)))
    pos = ((SIZE - glyph_size) // 2, (SIZE - glyph_size) // 2)
    tile.alpha_composite(glow, pos)
    tile.alpha_composite(glyph, pos)

    # hairline highlight along the top edge, like a glass tile
    shine = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ImageDraw.Draw(shine).rounded_rectangle((2, 2, SIZE - 3, SIZE - 3), radius=int(SIZE * RADIUS), outline=(255, 255, 255, 38), width=3)
    tile.alpha_composite(shine)

    mask = rounded_mask(SIZE, RADIUS)
    tile.putalpha(ImageChops.multiply(tile.getchannel("A"), mask))

    tile.resize((512, 512), Image.LANCZOS).save(ASSETS / "app_icon.png")
    sizes = [(s, s) for s in (16, 24, 32, 48, 64, 128, 256)]
    tile.save(ASSETS / "icon.ico", sizes=sizes)
    print("wrote", ASSETS / "app_icon.png", "and", ASSETS / "icon.ico")


if __name__ == "__main__":
    main()
