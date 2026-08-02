#!/usr/bin/env python3
"""Convert SRT captions into Primer Mall yellow pop ASS captions."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


TIME_RE = re.compile(
    r"(?P<start>\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(?P<end>\d{2}:\d{2}:\d{2},\d{3})"
)


HEADER = """[Script Info]
Title: Primer Mall Pop Captions
ScriptType: v4.00+
WrapStyle: 2
ScaledBorderAndShadow: yes
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Glow,Arial,{size},&H001FEBFF,&H000000FF,&H0000D7FF,&H00000000,-1,0,0,0,98,100,0,0,1,18,0,5,70,70,0,1
Style: WhiteRim,Arial,{size},&H001FEBFF,&H000000FF,&H00FFFFFF,&H00000000,-1,0,0,0,98,100,0,0,1,10,0,5,70,70,0,1
Style: PopMain,Arial,{size},&H001FEBFF,&H000000FF,&H00005CFF,&H00232010,-1,0,0,0,98,100,0,0,1,5,5,5,70,70,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def srt_time_to_ass(value: str) -> str:
    hms, ms = value.split(",")
    h, m, s = hms.split(":")
    centiseconds = int(ms) // 10
    return f"{int(h)}:{m}:{s}.{centiseconds:02d}"


def parse_srt(path: Path) -> list[tuple[str, str, str]]:
    text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    blocks = re.split(r"\n\s*\n", text.strip())
    items: list[tuple[str, str, str]] = []
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        time_index = next((i for i, line in enumerate(lines) if TIME_RE.search(line)), None)
        if time_index is None:
            continue
        match = TIME_RE.search(lines[time_index])
        assert match is not None
        caption = " ".join(lines[time_index + 1 :]).strip()
        if caption:
            items.append((match.group("start"), match.group("end"), caption))
    return items


def split_caption(text: str, max_chars: int) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_chars:
        return text
    words = text.split(" ")
    best_break = 1
    best_score = float("inf")
    for idx in range(1, len(words)):
        left = " ".join(words[:idx])
        right = " ".join(words[idx:])
        overflow = max(0, len(left) - max_chars) + max(0, len(right) - max_chars)
        balance = abs(len(left) - len(right)) / max(len(text), 1)
        score = overflow * 10 + balance
        if score < best_score:
            best_score = score
            best_break = idx
    return " ".join(words[:best_break]) + r"\N" + " ".join(words[best_break:])


def ass_escape(text: str) -> str:
    return text.replace("{", "(").replace("}", ")")


def build_ass(items: list[tuple[str, str, str]], size: int, x: int, y: int, max_chars: int) -> str:
    lines = [HEADER.format(size=size).rstrip()]
    for start, end, caption in items:
        start_ass = srt_time_to_ass(start)
        end_ass = srt_time_to_ass(end)
        body = ass_escape(split_caption(caption, max_chars))
        lines.append(
            f"Dialogue: 0,{start_ass},{end_ass},Glow,,0,0,0,,{{\\pos({x},{y})\\blur9}}{body}"
        )
        lines.append(
            f"Dialogue: 1,{start_ass},{end_ass},WhiteRim,,0,0,0,,{{\\pos({x},{y})}}{body}"
        )
        lines.append(
            f"Dialogue: 2,{start_ass},{end_ass},PopMain,,0,0,0,,{{\\pos({x},{y})}}{body}"
        )
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--srt", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--font-size", type=int, default=82)
    parser.add_argument("--x", type=int, default=540)
    parser.add_argument("--y", type=int, default=1425)
    parser.add_argument("--max-chars", type=int, default=28)
    args = parser.parse_args()

    items = parse_srt(args.srt)
    if not items:
        raise SystemExit(f"No SRT captions found in {args.srt}")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        build_ass(items, args.font_size, args.x, args.y, args.max_chars),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
