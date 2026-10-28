#!/usr/bin/env python3
"""Synthesizes the sound effects of test1 with ffmpeg: coloured noise mixed with triangle waves
between 440 Hz and 1.2 kHz. Writes 44.1 kHz mono 16-bit WAV files to assets/sound/.

Run from anywhere: `python3 tools/gen_sounds.py`.
"""

import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "sound"
RATE = 44100


def tri(freq: str) -> str:
    """A triangle wave in -1..1 whose phase argument is `freq` (an expression of `t`)."""
    return f"2/PI*asin(sin(2*PI*{freq}))"


# name: (noise colour, noise amplitude, triangle expression, duration in seconds, extra filters)
SOUNDS = {
    # A bell-like chime: pink noise under a decaying 880 Hz triangle.
    "chime": ("pink", 0.08, f"0.5*{tri('880*t')}*exp(-4*t)", 1.0, "afade=t=out:st=0.7:d=0.3"),
    # A swell: brown noise rising and falling, with a triangle sweeping 440 Hz → 1.2 kHz.
    "whoosh": (
        "brown",
        0.5,
        f"0.25*{tri('(440*t+380*t*t)')}*sin(PI*t/1.0)",
        1.0,
        "afade=t=in:d=0.4,afade=t=out:st=0.5:d=0.5",
    ),
    # Radio static: white noise with a 1.2 kHz triangle gated eight times a second.
    "static": ("white", 0.12, f"0.35*{tri('1200*t')}*gt(sin(2*PI*8*t),0)", 0.75, "afade=t=out:st=0.6:d=0.15"),
    # A short UI blip: blue noise and a 660 Hz triangle.
    "blip": ("blue", 0.05, f"0.5*{tri('660*t')}*exp(-12*t)", 0.25, "afade=t=out:st=0.2:d=0.05"),
    # A knock: a burst of brown noise with a fast-decaying 440 Hz triangle.
    "knock": ("brown", 0.9, f"0.6*{tri('440*t')}*exp(-30*t)", 0.2, "afade=t=out:st=0.05:d=0.15"),
    # The ending fanfare: pink noise and an A major triad of triangles (440, 554.37, 659.25 Hz).
    "fanfare": (
        "pink",
        0.06,
        f"0.2*({tri('440*t')}+{tri('554.37*t')}+{tri('659.25*t')})*exp(-1.2*t)",
        2.5,
        "afade=t=in:d=0.02,afade=t=out:st=2.0:d=0.5",
    ),
    # A looping ambience: violet and brown noise with a faint 440 Hz triangle (loops seamlessly:
    # 440 Hz has a whole number of periods in 8 s).
    "hum": ("brown", 0.25, f"0.06*{tri('440*t')}*(0.6+0.4*sin(2*PI*0.25*t))", 8.0, ""),
}


def render(name: str, color: str, amplitude: float, expr: str, seconds: float, filters: str) -> None:
    out = OUT / f"{name}.wav"
    noise = f"anoisesrc=color={color}:amplitude={amplitude}:duration={seconds}:sample_rate={RATE}:seed=7"
    wave = f"aevalsrc=exprs='{expr}':sample_rate={RATE}:duration={seconds}"
    graph = "[0:a][1:a]amix=inputs=2:normalize=0,alimiter=limit=0.9"
    if filters:
        graph += "," + filters
    subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", noise,
            "-f", "lavfi", "-i", wave,
            "-filter_complex", graph,
            "-ac", "1", "-c:a", "pcm_s16le", str(out),
        ],
        check=True,
    )
    print(f"wrote {out.relative_to(ROOT)}")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, spec in SOUNDS.items():
        render(name, *spec)


if __name__ == "__main__":
    main()
