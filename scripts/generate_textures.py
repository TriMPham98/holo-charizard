#!/usr/bin/env python3
"""Generate card textures as PNG files (run before or during Blender setup)."""
import colorsys
import math
import os

from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets", "textures")

HOLO_UV_X_MIN = 0.08
HOLO_UV_X_MAX = 0.92
HOLO_UV_Y_MIN = 0.36
HOLO_UV_Y_MAX = 0.78


def make_rainbow(path, width=1024, height=64):
    img = Image.new("RGB", (width, height))
    px = img.load()
    for y in range(height):
        for x in range(width):
            hue = x / width
            sat = 0.85 + 0.15 * math.sin(y / height * math.pi)
            r, g, b = colorsys.hsv_to_rgb(hue, sat, 1.0)
            px[x, y] = (int(r * 255), int(g * 255), int(b * 255))
    img.save(path)


def make_distortion(path, size=512):
    img = Image.new("RGB", (size, size))
    px = img.load()
    for y in range(size):
        for x in range(size):
            nx, ny = x / size, y / size
            v = (
                math.sin(nx * 28.0) * 0.5
                + math.sin(ny * 22.0 + nx * 9.0) * 0.3
                + math.sin((nx + ny) * 41.0) * 0.2
            )
            v = int((0.5 + v * 0.25) * 255)
            px[x, y] = (v, v, v)
    img.save(path)


def _try_font(size):
    for name in ("Helvetica.ttc", "Arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def make_card_face(path, width=744, height=1039):
    yellow = (250, 230, 46)
    cream = (245, 240, 210)
    dark = (40, 35, 30)

    img = Image.new("RGB", (width, height), yellow)
    draw = ImageDraw.Draw(img)

    margin_x = int(width * 0.06)
    margin_top = int(height * 0.04)
    margin_bottom = int(height * 0.22)
    art_top = int(height * HOLO_UV_Y_MAX)
    art_bottom = int(height * HOLO_UV_Y_MIN)
    art_left = int(width * HOLO_UV_X_MIN)
    art_right = int(width * HOLO_UV_X_MAX)

    # Art window background — fire gradient
    for y in range(art_bottom, art_top):
        ny = (y - art_bottom) / max(art_top - art_bottom, 1)
        for x in range(art_left, art_right):
            nx = (x - art_left) / max(art_right - art_left, 1)
            r = int(235 + 20 * math.sin(nx * 14.0 + ny * 8.0))
            g = int(70 + 80 * math.sin(nx * 7.0))
            b = int(10 + 30 * math.cos(ny * 10.0))
            if math.sin(nx * 100.0) * math.sin(ny * 100.0) > 0.84:
                r, g, b = 255, 255, 240
            img.putpixel((x, y), (r, g, b))

    # Inner frame lines
    draw.rectangle(
        (art_left, art_bottom, art_right, art_top),
        outline=(180, 140, 20),
        width=3,
    )

    # Stats box at bottom
    draw.rectangle(
        (margin_x, height - margin_bottom, width - margin_x, height - margin_top),
        fill=cream,
        outline=dark,
        width=2,
    )

    title_font = _try_font(42)
    small_font = _try_font(22)

    draw.text((margin_x + 12, margin_top), "Charizard", fill=dark, font=title_font)
    draw.text((width - 130, margin_top + 8), "HP 120", fill=dark, font=small_font)
    draw.text(
        (margin_x + 16, height - margin_bottom + 16),
        "Fire Spin   70",
        fill=dark,
        font=small_font,
    )
    draw.text(
        (margin_x + 16, height - margin_bottom + 48),
        "Flamethrower   90",
        fill=dark,
        font=small_font,
    )

    img.save(path)


def main():
    os.makedirs(ASSETS_DIR, exist_ok=True)
    make_rainbow(os.path.join(ASSETS_DIR, "Holo_Rainbow.png"))
    make_distortion(os.path.join(ASSETS_DIR, "Holo_Distortion.png"))
    make_card_face(os.path.join(ASSETS_DIR, "Card_Face_Placeholder.png"))
    print(f"Textures written to {ASSETS_DIR}")


if __name__ == "__main__":
    main()