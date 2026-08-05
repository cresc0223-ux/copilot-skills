#!/usr/bin/env python3
"""Normalize SRT or WebVTT cues into strict UTF-8 SRT."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from video_common import configure_stdout, normalized_text


TIME_RE = re.compile(
    r"(?P<start>(?:\d{1,2}:)?\d{2}:\d{2}[\.,]\d{3})\s*-->\s*"
    r"(?P<end>(?:\d{1,2}:)?\d{2}:\d{2}[\.,]\d{3})(?:\s+.*)?"
)


def to_ms(value: str) -> int:
    parts = value.replace(".", ",").split(":")
    if len(parts) == 2:
        parts.insert(0, "0")
    hours, minutes, seconds_ms = parts
    seconds, millis = seconds_ms.split(",")
    return ((int(hours) * 60 + int(minutes)) * 60 + int(seconds)) * 1000 + int(millis)


def from_ms(value: int) -> str:
    hours, remainder = divmod(value, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def clean(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value)
    return re.sub(r"\s+", " ", value).strip()


def parse_subtitles(path: Path) -> list[tuple[int, int, str]]:
    lines = path.read_text(encoding="utf-8-sig", errors="strict").replace("\r\n", "\n").splitlines()
    cues: list[tuple[int, int, str]] = []
    index = 0
    while index < len(lines):
        match = TIME_RE.match(lines[index].strip())
        if not match:
            index += 1
            continue
        index += 1
        body = []
        while index < len(lines) and lines[index].strip():
            body.append(lines[index].strip())
            index += 1
        text = clean(" ".join(body))
        start = to_ms(match.group("start"))
        end = to_ms(match.group("end"))
        if text:
            cues.append((start, end, text))
    return cues


def main() -> None:
    configure_stdout()
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="input", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--script", type=Path)
    parser.add_argument("--max-overlap-ms", type=int, default=150)
    args = parser.parse_args()

    cues = parse_subtitles(args.input)
    if not cues:
        raise SystemExit(f"No subtitle cues found: {args.input}")
    repaired = 0
    for index, (start, end, _) in enumerate(cues):
        previous_end = cues[index - 1][1] if index else -1
        if start < previous_end:
            overlap = previous_end - start
            if overlap > args.max_overlap_ms:
                raise SystemExit(f"Subtitle cues overlap by {overlap}ms; maximum repair is {args.max_overlap_ms}ms")
            previous_start, _, previous_text = cues[index - 1]
            if start <= previous_start:
                raise SystemExit("Subtitle cues are out of order")
            cues[index - 1] = (previous_start, start, previous_text)
            repaired += 1
        if end <= start:
            raise SystemExit("Subtitle cue has a non-positive duration")
    if args.script:
        source = args.script.read_text(encoding="utf-8-sig")
        combined = " ".join(text for _, _, text in cues)
        if normalized_text(source) != normalized_text(combined):
            raise SystemExit("Subtitle text does not match the source script")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    blocks = [f"{index}\n{from_ms(start)} --> {from_ms(end)}\n{text}\n" for index, (start, end, text) in enumerate(cues, 1)]
    args.out.write_text("\n".join(blocks), encoding="utf-8")
    print(f"wrote {len(cues)} cues to {args.out}; repaired {repaired} minor overlaps")


if __name__ == "__main__":
    main()
