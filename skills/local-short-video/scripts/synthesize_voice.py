#!/usr/bin/env python3
"""Generate edge-tts voice audio and WebVTT timing from one final script."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from video_common import configure_stdout, normalized_text, run, write_json


def vtt_text(path: Path) -> str:
    lines = path.read_text(encoding="utf-8-sig", errors="replace").replace("\r\n", "\n").splitlines()
    visible = []
    in_cue = False
    for line in lines:
        stripped = line.strip()
        if "-->" in stripped:
            in_cue = True
            continue
        if not stripped:
            in_cue = False
        elif in_cue and not stripped.startswith(("NOTE", "STYLE", "REGION")):
            visible.append(stripped)
    return " ".join(visible)


def main() -> None:
    configure_stdout()
    parser = argparse.ArgumentParser()
    parser.add_argument("--script", required=True, type=Path)
    parser.add_argument("--voice", required=True)
    parser.add_argument("--rate", default="+8%")
    parser.add_argument("--pitch", default="+0Hz")
    parser.add_argument("--media", required=True, type=Path)
    parser.add_argument("--vtt", required=True, type=Path)
    parser.add_argument("--metadata", type=Path)
    args = parser.parse_args()

    text = args.script.read_text(encoding="utf-8-sig").strip()
    if not text:
        raise SystemExit(f"Script is empty: {args.script}")
    args.media.parent.mkdir(parents=True, exist_ok=True)
    args.vtt.parent.mkdir(parents=True, exist_ok=True)

    listed = run([sys.executable, "-m", "edge_tts", "--list-voices"], check=False)
    if listed.returncode != 0:
        raise SystemExit("edge-tts could not list voices: " + (listed.stderr or listed.stdout).strip())
    if args.voice not in listed.stdout:
        raise SystemExit(f"Selected edge-tts voice is unavailable: {args.voice}")

    command = [
        sys.executable, "-m", "edge_tts",
        "--voice", args.voice,
        f"--rate={args.rate}",
        f"--pitch={args.pitch}",
        "--text", text,
        "--write-media", str(args.media),
        "--write-subtitles", str(args.vtt),
    ]
    proc = run(command, check=False)
    if proc.returncode != 0:
        raise SystemExit("edge-tts generation failed: " + (proc.stderr or proc.stdout).strip())
    if not args.media.exists() or args.media.stat().st_size < 512:
        raise SystemExit("edge-tts produced empty or invalid audio")
    if not args.vtt.exists() or "-->" not in args.vtt.read_text(encoding="utf-8-sig", errors="replace"):
        raise SystemExit("edge-tts did not produce usable WebVTT timing")

    timed_text = vtt_text(args.vtt)
    if normalized_text(timed_text) != normalized_text(text):
        raise SystemExit("TTS timing text does not match the source script exactly")
    metadata = args.metadata or args.media.with_name("selected_voice.json")
    write_json(metadata, {
        "provider": "edge-tts",
        "voice": args.voice,
        "rate": args.rate,
        "pitch": args.pitch,
        "script": str(args.script.resolve()),
        "media": str(args.media.resolve()),
        "timing": str(args.vtt.resolve()),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "text_match": True,
    })
    print(metadata)


if __name__ == "__main__":
    main()

