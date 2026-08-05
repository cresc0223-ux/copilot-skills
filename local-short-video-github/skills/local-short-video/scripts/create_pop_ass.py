#!/usr/bin/env python3
"""Create safe-zone ASS captions from normalized SRT or WebVTT."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from normalize_subtitles import parse_subtitles
from video_common import configure_stdout


STYLES = {
    "pop-yellow": ("&H0025E9FF", "&H000052B8", "&H00101010"),
    "clean-white": ("&H00FFFFFF", "&H00202020", "&H00101010"),
    "cyan-tech": ("&H00FFE066", "&H00602010", "&H00101010"),
    "pink-lifestyle": ("&H00E8A0FF", "&H00702080", "&H00101010"),
    "green-value": ("&H009CFFB4", "&H00306020", "&H00101010"),
}


def ass_time(milliseconds: int) -> str:
    hours, remainder = divmod(max(0, milliseconds), 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, millis = divmod(remainder, 1000)
    return f"{hours}:{minutes:02d}:{seconds:02d}.{millis // 10:02d}"


def tokenize(text: str) -> list[str]:
    if " " in text.strip():
        return text.split()
    return list(text.strip())


def make_blocks(text: str, max_chars: int) -> list[str]:
    tokens = tokenize(re.sub(r"\s+", " ", text).strip())
    separator = " " if " " in text.strip() else ""
    lines: list[str] = []
    current: list[str] = []
    for token in tokens:
        candidate = separator.join([*current, token])
        if current and len(candidate) > max_chars:
            lines.append(separator.join(current))
            current = [token]
        else:
            current.append(token)
    if current:
        lines.append(separator.join(current))
    return [r"\N".join(lines[index:index + 2]) for index in range(0, len(lines), 2)] or [""]


def escape_ass(value: str) -> str:
    return value.replace("{", "(").replace("}", ")")


def main() -> None:
    configure_stdout()
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="input", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--style", choices=sorted(STYLES), default="pop-yellow")
    parser.add_argument("--font", default="Arial")
    parser.add_argument("--font-size", type=int, default=78)
    parser.add_argument("--width", type=int, default=1080)
    parser.add_argument("--height", type=int, default=1920)
    parser.add_argument("--position", choices=["upper", "center", "lower"], default="lower")
    parser.add_argument("--x", type=int)
    parser.add_argument("--y", type=int)
    parser.add_argument("--safe-margin", type=int, default=70)
    parser.add_argument("--max-chars", type=int, default=30)
    args = parser.parse_args()

    cues = parse_subtitles(args.input)
    if not cues:
        raise SystemExit(f"No subtitle cues found: {args.input}")
    x = args.x if args.x is not None else args.width // 2
    default_y = {"upper": int(args.height * 0.20), "center": args.height // 2, "lower": int(args.height * 0.74)}
    y = args.y if args.y is not None else default_y[args.position]
    if not (args.safe_margin <= x <= args.width - args.safe_margin):
        raise SystemExit("Subtitle x position is outside the horizontal safe zone")
    if not (args.safe_margin <= y <= args.height - args.safe_margin):
        raise SystemExit("Subtitle y position is outside the vertical safe zone")

    primary, outline, shadow = STYLES[args.style]
    header = f"""[Script Info]
Title: Local Short Video Captions
ScriptType: v4.00+
WrapStyle: 2
ScaledBorderAndShadow: yes
PlayResX: {args.width}
PlayResY: {args.height}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,{args.font},{args.font_size},{primary},&H000000FF,{outline},{shadow},-1,0,0,0,100,100,0,0,1,5,3,5,{args.safe_margin},{args.safe_margin},0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [header.rstrip()]
    for start, end, text in cues:
        blocks = make_blocks(text, args.max_chars)
        span = max(1, end - start)
        for index, block in enumerate(blocks):
            block_start = start + span * index // len(blocks)
            block_end = end if index == len(blocks) - 1 else start + span * (index + 1) // len(blocks)
            body = escape_ass(block)
            lines.append(f"Dialogue: 0,{ass_time(block_start)},{ass_time(block_end)},Caption,,0,0,0,,{{\\pos({x},{y})}}{body}")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()

