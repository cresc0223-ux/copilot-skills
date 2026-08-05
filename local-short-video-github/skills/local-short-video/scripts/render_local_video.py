#!/usr/bin/env python3
"""Render a mobile-compatible short video from local media, voice, and ASS."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

from video_common import (
    VIDEO_EXTS,
    configure_stdout,
    find_ffmpeg,
    find_ffprobe,
    load_json,
    media_summary,
    run,
    write_json,
)


def ass_filter_path(path: Path) -> str:
    return path.resolve().as_posix().replace(":", r"\:").replace("'", r"\'")


def segment_durations(count: int, total: float, pacing: str) -> list[float]:
    if count <= 0:
        return []
    if pacing == "energetic":
        weights = [0.75, 1.0, 0.8, 1.2, 0.9, 1.1]
    elif pacing == "tutorial":
        weights = [1.0, 1.2, 1.1, 1.3]
    else:
        weights = [0.9, 1.1, 1.0, 1.2, 0.8]
    raw = [weights[index % len(weights)] for index in range(count)]
    scale = total / sum(raw)
    durations = [round(value * scale, 3) for value in raw]
    durations[-1] = round(durations[-1] + total - sum(durations), 3)
    return durations


def build_inputs(ffmpeg: str, assets: list[dict], durations: list[float]) -> list[str]:
    command = [ffmpeg, "-y", "-hide_banner"]
    for asset, duration in zip(assets, durations):
        source = Path(asset["path"])
        if source.suffix.lower() in VIDEO_EXTS:
            command += ["-ss", str(asset.get("source_start", 0)), "-t", f"{duration + 0.2:.3f}", "-i", str(source)]
        else:
            command += ["-loop", "1", "-t", f"{duration:.3f}", "-i", str(source)]
    return command


def build_filter(assets: list[dict], durations: list[float], width: int, height: int, fps: int) -> str:
    parts = []
    labels = []
    for index, (asset, duration) in enumerate(zip(assets, durations)):
        common = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},setsar=1"
        if Path(asset["path"]).suffix.lower() in VIDEO_EXTS:
            chain = (
                f"[{index}:v]{common},fps={fps},eq=contrast=1.02:saturation=1.04,"
                f"trim=duration={duration:.3f},setpts=PTS-STARTPTS,"
                f"tpad=stop_mode=clone:stop_duration={duration:.3f},trim=duration={duration:.3f}[v{index}]"
            )
        else:
            frames = max(1, math.ceil(duration * fps))
            chain = (
                f"[{index}:v]{common},"
                f"zoompan=z='min(zoom+0.0007,1.07)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                f"d={frames}:s={width}x{height}:fps={fps},trim=duration={duration:.3f},setpts=PTS-STARTPTS[v{index}]"
            )
        parts.append(chain)
        labels.append(f"[v{index}]")
    parts.append(f"{''.join(labels)}concat=n={len(labels)}:v=1:a=0[vbase]")
    return ";".join(parts)


def write_usage(path: Path, assets: list[dict], durations: list[float]) -> None:
    start = 0.0
    records = []
    for asset, duration in zip(assets, durations):
        record = dict(asset)
        record.update({
            "timeline_start": round(start, 3),
            "timeline_end": round(start + duration, 3),
            "usage_count_this_video": 1,
        })
        records.append(record)
        start += duration
    manifest = {"assets": records}
    write_json(path, manifest)
    csv_path = path.with_suffix(".csv")
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        fields = ["path", "relative_path", "kind", "role", "source_start", "timeline_start", "timeline_end", "usage_count_this_video"]
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def main() -> None:
    configure_stdout()
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--voice", required=True, type=Path)
    parser.add_argument("--ass", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--base-out", type=Path)
    parser.add_argument("--used-assets", type=Path)
    parser.add_argument("--contact-sheet", type=Path)
    parser.add_argument("--duration", type=float, default=30.0)
    parser.add_argument("--width", type=int, default=1080)
    parser.add_argument("--height", type=int, default=1920)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--pacing", choices=["energetic", "showcase", "tutorial"], default="showcase")
    parser.add_argument("--ffmpeg")
    parser.add_argument("--ffprobe")
    args = parser.parse_args()

    ffmpeg = args.ffmpeg or find_ffmpeg()
    ffprobe = args.ffprobe or find_ffprobe(ffmpeg=ffmpeg)
    if not ffmpeg:
        raise SystemExit("FFmpeg not found")
    if not args.voice.exists() or not args.ass.exists():
        raise SystemExit("Voice audio or ASS captions are missing")
    voice_duration = media_summary(args.voice, ffprobe, ffmpeg).get("duration", 0)
    if voice_duration and voice_duration > args.duration + 0.25:
        raise SystemExit(f"Voice duration {voice_duration:.2f}s exceeds target {args.duration:.2f}s")

    data = load_json(args.manifest)
    assets = [item for item in data.get("assets", []) if Path(item.get("path", "")).exists()]
    if not assets:
        raise SystemExit("Manifest has no usable assets")
    min_shot = {"energetic": 1.2, "showcase": 1.7, "tutorial": 2.4}[args.pacing]
    max_assets = max(1, int(args.duration / min_shot))
    assets = assets[:max_assets]
    durations = segment_durations(len(assets), args.duration, args.pacing)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    base_out = args.base_out or args.out.with_name("base_muted.mp4")
    used_assets = args.used_assets or args.out.with_name("used_assets.json")
    contact_sheet = args.contact_sheet or args.out.with_name("preview_final_contact_sheet.jpg")
    command = build_inputs(ffmpeg, assets, durations)
    command += [
        "-filter_complex", build_filter(assets, durations, args.width, args.height, args.fps),
        "-map", "[vbase]", "-t", f"{args.duration:.3f}", "-an",
        "-r", str(args.fps), "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", str(base_out),
    ]
    proc = run(command, check=False)
    if proc.returncode != 0:
        raise SystemExit(proc.stderr.strip())

    ass_path = ass_filter_path(args.ass)
    final_command = [
        ffmpeg, "-y", "-hide_banner", "-i", str(base_out), "-i", str(args.voice),
        "-filter_complex", f"[0:v]ass='{ass_path}'[v];[1:a]loudnorm=I=-16:TP=-1.5:LRA=11,apad=pad_dur={args.duration:.3f}[a]",
        "-map", "[v]", "-map", "[a]", "-t", f"{args.duration:.3f}", "-r", str(args.fps),
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-profile:a", "aac_low", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-movflags", "+faststart", str(args.out),
    ]
    proc = run(final_command, check=False)
    if proc.returncode != 0:
        raise SystemExit(proc.stderr.strip())

    interval = max(args.duration / 6.0, 0.5)
    sheet_command = [
        ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(args.out),
        "-vf", f"fps=1/{interval:.3f},scale=216:384,tile=3x2", "-frames:v", "1", "-update", "1", str(contact_sheet),
    ]
    proc = run(sheet_command, check=False)
    if proc.returncode != 0:
        raise SystemExit("Final contact sheet failed: " + proc.stderr.strip())
    write_usage(used_assets, assets, durations)
    print(args.out)


if __name__ == "__main__":
    main()
