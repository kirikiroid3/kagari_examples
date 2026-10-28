#!/usr/bin/env python3
"""Generates the voiced lines of test1 with Cartesia TTS into assets/characters/<c>/voice/.

The API key is `CARTESIA_KEY`, from the environment or from the `.env` file at the root of the
kagari_examples repository. Existing files are kept; pass `--force` to regenerate them all.
Run from anywhere: `python3 tools/gen_voices.py`. Needs ffmpeg.

Each transcript is the plain text of a line in src/scenario/; keep them in sync.
"""

import concurrent.futures
import json
import os
import pathlib
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
ENV_FILE = ROOT.parent / ".env"
API = "https://api.cartesia.ai/tts/bytes"
API_VERSION = "2026-08-14"
MODEL = "sonic-3.6"

# Character → Cartesia voice (Japanese voices of the Cartesia library).
VOICES = {
    "a": "31c55968-a9f4-4115-8831-3a16952179c8",  # Ayumi: upbeat female
    "i": "c7eafe22-8b71-40cd-850b-c5a3bbd8f8d2",  # Emi: soft, timid female
    "u": "9436e723-612d-4114-aeb0-fa00d4d639bf",  # Katsuya: lively male
    "e": "6b92f628-be90-497c-8f4c-3b035002df71",  # Kenji: calm, deep male
    "o": "2b568345-1d48-4047-b25f-7baccf842eb0",  # Yumiko: friendly female
}

# (character, file stem, transcript)
LINES = [
    ("a", "a", "ここは「あ」です。最初のメッセージなので、前のメッセージはありません。次のメッセージは「い」です。"),
    ("i", "i", "ここは「い」です。前のメッセージは「あ」、次のメッセージは「う」です。"),
    ("u", "u", "ここは「う」です。前のメッセージは「い」です。次のメッセージは「え」です。"),
    ("e", "e", "ここは「え」です。前のメッセージは「う」です。次のメッセージは「お」です。"),
    ("o", "o", "ここは「お」です。前のメッセージは「え」です。次は「か」か「が」、どちらかを選んでください。"),
    ("o", "ki", "ここは「き」です。前のメッセージは「か」です。次のメッセージは「く」です。"),
    ("e", "ga", "ここは「が」です。前のメッセージは「お」です。次のメッセージは「ぎ」です。"),
    ("a", "sa", "ここは「さ」です。前のメッセージは「こ」です。次のメッセージは「し」です。"),
    ("i", "za", "ここは「ざ」です。前のメッセージは「こ」か「ご」です。次のメッセージは「じ」です。"),
    ("u", "ta", "ここは「た」です。前のメッセージは「そ」か「ぞ」です。次のメッセージは「ち」です。"),
    ("o", "da", "ここは「だ」です。前のメッセージは「ぞ」です。次のメッセージは「ぢ」です。"),
    ("e", "na", "ここは「な」です。前のメッセージは「と」か「ど」です。次のメッセージは「に」です。"),
    ("a", "ha", "ここは「は」です。前のメッセージは「の」です。次のメッセージは「ひ」です。"),
    ("e", "ba", "ここは「ば」です。前のメッセージは「の」です。次のメッセージは「び」です。"),
    ("i", "pa", "ここは「ぱ」です。前のメッセージは「の」です。次のメッセージは「ぴ」です。"),
    ("u", "ma", "ここは「ま」です。前のメッセージは「の」です。次のメッセージは「み」です。"),
    ("o", "ra", "ここは「ら」です。前のメッセージは「も」です。次は「り」か「る」、ランダムに決まります。"),
    ("a", "wa", "ここは「わ」です。前のメッセージは「ろ」です。次のメッセージは「ゐ」です。"),
    ("i", "ya", "ここは「や」です。前のメッセージは「ろ」です。次のメッセージはありません。エンディング「や」です!"),
    ("o", "wo", "ここは「を」です。前のメッセージは「ゑ」です。これでおしまい、エンディング「を」です。"),
    ("u", "n", "ここは「ん」です。前のメッセージは「ろ」です。最後の文字、エンディング「ん」です!"),
]


def api_key() -> str:
    key = os.environ.get("CARTESIA_KEY")
    if not key and ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            name, sep, value = line.partition("=")
            if sep and name.strip() == "CARTESIA_KEY":
                key = value.strip().strip("'\"")
    if not key:
        sys.exit(f"CARTESIA_KEY is not set (environment or {ENV_FILE})")
    return key


def generate(key: str, character: str, stem: str, transcript: str) -> str:
    out = ROOT / "assets" / "characters" / character / "voice" / f"{stem}.wav"
    body = {
        "model_id": MODEL,
        "transcript": transcript,
        "voice": {"id": VOICES[character]},
        "language": "ja",
        "output_format": {"container": "wav", "encoding": "pcm_s16le", "sample_rate": 44100},
    }
    request = urllib.request.Request(
        API,
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {key}",
            "Cartesia-Version": API_VERSION,
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            audio = response.read()
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"{out.name}: HTTP {error.code}: {error.read()[:300]!r}") from error
    out.parent.mkdir(parents=True, exist_ok=True)
    # The API streams its WAV with unknown sizes (0xFFFFFFFF) in the RIFF and data headers;
    # ffmpeg rewrites the file with the real sizes, which strict decoders need.
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", "pipe:0",
         "-map_metadata", "-1", "-c:a", "pcm_s16le", str(out)],
        input=audio,
        check=True,
    )
    return str(out.relative_to(ROOT))


def main() -> None:
    force = "--force" in sys.argv[1:]
    key = api_key()
    todo = [
        line
        for line in LINES
        if force or not (ROOT / "assets" / "characters" / line[0] / "voice" / f"{line[1]}.wav").exists()
    ]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for path in pool.map(lambda line: generate(key, *line), todo):
            print(f"wrote {path}")


if __name__ == "__main__":
    main()
