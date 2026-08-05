#!/usr/bin/env python3
"""List locale-matched edge-tts voices and render comparable samples."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from video_common import configure_stdout, run, write_json


VOICE_RE = re.compile(r"^(?P<name>[a-z]{2,3}-[A-Z]{2,4}-\S+Neural)\s+(?P<gender>Female|Male)\b")


def main() -> None:
    configure_stdout()
    parser = argparse.ArgumentParser()
    parser.add_argument("--locale", required=True, help="Locale prefix such as es-MX, en-US, or zh-CN")
    parser.add_argument("--text", required=True)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--limit", type=int, default=4)
    parser.add_argument("--rate", default="+8%")
    parser.add_argument("--pitch", default="+0Hz")
    args = parser.parse_args()

    listed = run([sys.executable, "-m", "edge_tts", "--list-voices"], check=False)
    if listed.returncode != 0:
        raise SystemExit((listed.stderr or listed.stdout).strip())
    voices = []
    for line in listed.stdout.splitlines():
        match = VOICE_RE.match(line.strip())
        if match and match.group("name").casefold().startswith(args.locale.casefold()):
            voices.append(match.groupdict())
    if not voices:
        raise SystemExit(f"No edge-tts voices found for locale: {args.locale}")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for voice in voices[: max(1, args.limit)]:
        media = args.out_dir / f"{voice['name']}.mp3"
        command = [
            sys.executable, "-m", "edge_tts",
            "--voice", voice["name"],
            f"--rate={args.rate}",
            f"--pitch={args.pitch}",
            "--text", args.text,
            "--write-media", str(media),
        ]
        proc = run(command, check=False)
        results.append({
            **voice,
            "file": str(media),
            "ok": proc.returncode == 0 and media.exists() and media.stat().st_size > 512,
            "error": (proc.stderr or proc.stdout).strip()[-500:] if proc.returncode else "",
        })
    manifest = args.out_dir / "voice_candidates.json"
    write_json(manifest, {"locale": args.locale, "rate": args.rate, "pitch": args.pitch, "candidates": results})
    if not any(item["ok"] for item in results):
        raise SystemExit("All voice auditions failed")
    print(manifest)


if __name__ == "__main__":
    main()

