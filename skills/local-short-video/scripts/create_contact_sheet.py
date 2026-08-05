#!/usr/bin/env python3
"""Create an FFmpeg contact sheet from a selected asset manifest."""

from __future__ import annotations

import argparse
import math
import tempfile
from pathlib import Path

from video_common import VIDEO_EXTS, configure_stdout, find_ffmpeg, load_json, run


def main() -> None:
    configure_stdout()
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--ffmpeg")
    parser.add_argument("--columns", type=int, default=3)
    parser.add_argument("--thumb-width", type=int, default=320)
    parser.add_argument("--thumb-height", type=int, default=568)
    args = parser.parse_args()

    ffmpeg = args.ffmpeg or find_ffmpeg()
    if not ffmpeg:
        raise SystemExit("FFmpeg not found")
    data = load_json(args.manifest)
    assets = data.get("assets", [])
    if not assets:
        raise SystemExit("Manifest has no assets")
    args.out.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="local-video-sheet-") as tmp:
        thumbs: list[Path] = []
        for index, asset in enumerate(assets):
            source = Path(asset["path"])
            thumb = Path(tmp) / f"{index:03d}.jpg"
            command = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error"]
            if source.suffix.lower() in VIDEO_EXTS:
                command += ["-ss", str(asset.get("source_start", 0.5)), "-i", str(source)]
            else:
                command += ["-i", str(source)]
            command += [
                "-frames:v", "1",
                "-vf", f"scale={args.thumb_width}:{args.thumb_height}:force_original_aspect_ratio=decrease,pad={args.thumb_width}:{args.thumb_height}:(ow-iw)/2:(oh-ih)/2:black",
                str(thumb),
            ]
            proc = run(command, check=False)
            if proc.returncode == 0 and thumb.exists():
                thumbs.append(thumb)
        if not thumbs:
            raise SystemExit("Could not extract any contact-sheet thumbnails")

        columns = max(1, min(args.columns, len(thumbs)))
        rows = math.ceil(len(thumbs) / columns)
        command = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error"]
        for thumb in thumbs:
            command += ["-i", str(thumb)]
        if len(thumbs) == 1:
            command += ["-frames:v", "1", str(args.out)]
        else:
            layout = "|".join(f"{(index % columns) * args.thumb_width}_{(index // columns) * args.thumb_height}" for index in range(len(thumbs)))
            inputs = "".join(f"[{index}:v]" for index in range(len(thumbs)))
            command += [
                "-filter_complex", f"{inputs}xstack=inputs={len(thumbs)}:layout={layout}:fill=black[out]",
                "-map", "[out]", "-frames:v", "1", str(args.out),
            ]
        proc = run(command, check=False)
        if proc.returncode != 0:
            raise SystemExit(proc.stderr.strip())
    print(args.out)


if __name__ == "__main__":
    main()
