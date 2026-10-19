"""Builds the app icons from the transparent logo in assets/logo.png.

    python tools/make_icons.py

Writes assets/app_icon.png (iOS-style rounded square, light, with a soft shadow)
and assets/icon.ico (16-256 px, used for the exe and the window). The app UI
itself uses the transparent logo.png directly. Committed outputs; rerun only
when the logo changes.
"""

from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ASSETS = Path(__file__).resolve().parent.parent / "assets"
SIZE = 1024
RADIUS = 0.2237          # Apple's icon corner radius as a fraction of the side
GLYPH_SCALE = 0.68
MARGIN = 0.05            # transparent border around the tile, room for the shadow


def gradient(size, top, bottom):
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
    inner = int(SIZE * (1 - 2 * MARGIN))
    tile = gradient(inner, (255, 255, 255), (232, 232, 240)).convert("RGBA")

    glyph_size = int(inner * GLYPH_SCALE)
    glyph = logo.resize((glyph_size, glyph_size), Image.LANCZOS)
    tile.alpha_composite(glyph, ((inner - glyph_size) // 2, (inner - glyph_size) // 2))

    # hairline edge so a white tile still reads on a white taskbar or page
    edge = Image.new("RGBA", (inner, inner), (0, 0, 0, 0))
    ImageDraw.Draw(edge).rounded_rectangle((1, 1, inner - 2, inner - 2), radius=int(inner * RADIUS),
                                           outline=(0, 0, 0, 34), width=3)
    tile.alpha_composite(edge)
    tile.putalpha(ImageChops.multiply(tile.getchannel("A"), rounded_mask(inner, RADIUS)))

    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    offset = (SIZE - inner) // 2
    shadow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    shadow.paste((0, 0, 0, 70), (offset, offset + int(SIZE * 0.012)), rounded_mask(inner, RADIUS))
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(SIZE * 0.018)))
    canvas.alpha_composite(tile, (offset, offset))

    canvas.resize((512, 512), Image.LANCZOS).save(ASSETS / "app_icon.png")
    canvas.save(ASSETS / "icon.ico", sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)])
    print("wrote", ASSETS / "app_icon.png", "and", ASSETS / "icon.ico")


if __name__ == "__main__":
    main()
