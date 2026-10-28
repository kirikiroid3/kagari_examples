#!/usr/bin/env python3
"""Writes the SVG sources of test1 to art/ and converts them to PNG in assets/ with `magick`.

Run from anywhere: `python3 tools/gen_images.py`. Needs ImageMagick 7 with librsvg and the
"Noto Sans CJK JP" font.
"""

import colorsys
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
ART = ROOT / "art"
ASSETS = ROOT / "assets"
FONT = "Noto Sans CJK JP"

# Characters: (directory, kana, romaji, colour, darker colour).
CHARACTERS = [
    ("a", "あ", "A", "#E53935", "#8E1B18"),
    ("i", "い", "I", "#FBC02D", "#8A6400"),
    ("u", "う", "U", "#43A047", "#1B5E20"),
    ("e", "え", "E", "#1E88E5", "#0D47A1"),
    ("o", "お", "O", "#8E24AA", "#4A148C"),
]

# Backgrounds: (file stem, big kana, title, the row's kana).
ROWS = [
    ("a", "あ", "あ行 · a-row", "あ い う え お"),
    ("ka", "か", "か行 · ka-row", "か き く け こ"),
    ("ga", "が", "が行 · ga-row", "が ぎ ぐ げ ご"),
    ("sa", "さ", "さ行 · sa-row", "さ し す せ そ"),
    ("za", "ざ", "ざ行 · za-row", "ざ じ ず ぜ ぞ"),
    ("ta", "た", "た行 · ta-row", "た ち つ て と"),
    ("da", "だ", "だ行 · da-row", "だ ぢ づ で ど"),
    ("na", "な", "な行 · na-row", "な に ぬ ね の"),
    ("ha", "は", "は行 · ha-row", "は ひ ふ へ ほ"),
    ("ba", "ば", "ば行 · ba-row", "ば び ぶ べ ぼ"),
    ("pa", "ぱ", "ぱ行 · pa-row", "ぱ ぴ ぷ ぺ ぽ"),
    ("ma", "ま", "ま行 · ma-row", "ま み む め も"),
    ("ra", "ら", "ら行 · ra-row", "ら り る れ ろ"),
    ("wa", "わ", "わ行 · wa-row", "わ ゐ ゑ を"),
]

ENDINGS = [
    ("end_ya", "や", "#F57C00"),
    ("end_wo", "を", "#00897B"),
    ("end_n", "ん", "#37474F"),
]


def hsl(h: float, s: float, l: float) -> str:
    r, g, b = colorsys.hls_to_rgb(h % 1.0, l, s)
    return f"#{round(r * 255):02X}{round(g * 255):02X}{round(b * 255):02X}"


def character_svg(kana: str, romaji: str, color: str, dark: str, happy: bool) -> str:
    extras = ""
    if happy:
        extras = f"""
  <ellipse cx="120" cy="270" rx="26" ry="14" fill="#FF8A80" opacity="0.8"/>
  <ellipse cx="280" cy="270" rx="26" ry="14" fill="#FF8A80" opacity="0.8"/>
  <text x="352" y="96" font-family="{FONT}" font-size="72" font-weight="bold" fill="{dark}" text-anchor="middle">!</text>
  <text x="52" y="110" font-family="{FONT}" font-size="56" fill="{dark}" text-anchor="middle">♪</text>"""
    size = 210 if happy else 190
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="280" height="448" viewBox="0 0 400 640">
  <path d="M70 640 L95 420 Q200 370 305 420 L330 640 Z" fill="{color}" stroke="{dark}" stroke-width="6"/>
  <circle cx="200" cy="210" r="175" fill="{color}" stroke="{dark}" stroke-width="6"/>
  <circle cx="200" cy="215" r="138" fill="#FFF8F0" stroke="{dark}" stroke-width="4"/>
  <text x="200" y="68" font-family="{FONT}" font-size="34" font-weight="bold" fill="#FFFFFF" text-anchor="middle">{romaji}</text>
  <text x="200" y="{215 + size * 0.36:.0f}" font-family="{FONT}" font-size="{size}" font-weight="bold" fill="{dark}" text-anchor="middle">{kana}</text>{extras}
</svg>
"""


def background_svg(kana: str, title: str, row: str, base: str, light: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{light}"/>
      <stop offset="1" stop-color="{base}"/>
    </linearGradient>
  </defs>
  <rect width="1280" height="720" fill="url(#g)"/>
  <g stroke="#FFFFFF" stroke-opacity="0.15" stroke-width="2">
    {"".join(f'<line x1="{x}" y1="0" x2="{x - 400}" y2="720"/>' for x in range(0, 1700, 80))}
  </g>
  <text x="1010" y="560" font-family="{FONT}" font-size="560" font-weight="bold" fill="#FFFFFF" fill-opacity="0.28" text-anchor="middle">{kana}</text>
  <text x="40" y="72" font-family="{FONT}" font-size="48" font-weight="bold" fill="#FFFFFF" stroke="#00000055" stroke-width="2">{title}<tspan font-weight="normal" fill-opacity="0.9" dx="32">{row}</tspan></text>
</svg>
"""


def ending_svg(kana: str, color: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">
  <rect width="1280" height="720" fill="{color}"/>
  <circle cx="640" cy="330" r="250" fill="#FFFFFF" fill-opacity="0.15"/>
  <text x="640" y="460" font-family="{FONT}" font-size="360" font-weight="bold" fill="#FFFFFF" text-anchor="middle">{kana}</text>
  <text x="640" y="660" font-family="{FONT}" font-size="64" font-weight="bold" fill="#FFFFFF" text-anchor="middle">END 「{kana}」</text>
</svg>
"""


def title_svg() -> str:
    circles = "".join(
        f'<circle cx="{240 + k * 200}" cy="300" r="85" fill="{c}" stroke="{d}" stroke-width="5"/>'
        f'<text x="{240 + k * 200}" y="335" font-family="{FONT}" font-size="100" font-weight="bold" '
        f'fill="#FFFFFF" text-anchor="middle">{kana}</text>'
        for k, (_, kana, _, c, d) in enumerate(CHARACTERS)
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">
  <rect width="1280" height="720" fill="#1F2235"/>
  <text x="640" y="150" font-family="{FONT}" font-size="80" font-weight="bold" fill="#FFFFFF" text-anchor="middle">Kagari test1</text>
  {circles}
  <text x="640" y="440" font-family="{FONT}" font-size="36" fill="#C5CAE9" text-anchor="middle">五十音の partial order テスト</text>
</svg>
"""


def write(svg_rel: str, svg: str, png_rel: str) -> None:
    svg_path = ART / svg_rel
    png_path = ASSETS / png_rel
    svg_path.parent.mkdir(parents=True, exist_ok=True)
    png_path.parent.mkdir(parents=True, exist_ok=True)
    svg_path.write_text(svg, encoding="utf-8")
    subprocess.run(["magick", "-background", "none", str(svg_path), str(png_path)], check=True)
    print(f"wrote {png_path.relative_to(ROOT)}")


def main() -> None:
    for name, kana, romaji, color, dark in CHARACTERS:
        for face, happy in (("normal", False), ("happy", True)):
            svg = character_svg(kana, romaji, color, dark, happy)
            write(f"characters/{name}_{face}.svg", svg, f"characters/{name}/image/{face}.png")
    for k, (stem, kana, title, row) in enumerate(ROWS):
        hue = k / len(ROWS)
        svg = background_svg(kana, title, row, hsl(hue, 0.45, 0.35), hsl(hue + 0.05, 0.55, 0.62))
        write(f"bgimage/{stem}.svg", svg, f"bgimage/{stem}.png")
    for stem, kana, color in ENDINGS:
        write(f"bgimage/{stem}.svg", ending_svg(kana, color), f"bgimage/{stem}.png")
    write("bgimage/title.svg", title_svg(), "bgimage/title.png")


if __name__ == "__main__":
    main()
