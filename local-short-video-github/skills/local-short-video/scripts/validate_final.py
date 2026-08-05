#!/usr/bin/env python3
"""Validate mobile media properties, audio, frames, and subtitle integrity."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

from normalize_subtitles import parse_subtitles
from video_common import configure_stdout, find_ffmpeg, find_ffprobe, normalized_text, probe_media, run, write_json


def rate(value: str) -> float:
    if not value or value == "0/0":
        return 0.0
    if "/" in value:
        numerator, denominator = value.split("/", 1)
        return float(numerator) / float(denominator or 1)
    return float(value)


def ffmpeg_fallback(ffmpeg: str, video: Path) -> dict:
    proc = run([ffmpeg, "-hide_banner", "-i", str(video), "-f", "null", os.devnull], check=False)
    text = proc.stderr
    duration_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", text)
    duration = 0.0
    if duration_match:
        hours, minutes, seconds = duration_match.groups()
        duration = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    video_match = re.search(r"Video:\s*([^,\n]+),\s*([^,\n]+),\s*(\d+)x(\d+).*?,\s*([\d.]+)\s*fps", text)
    audio_match = re.search(r"Audio:\s*([^,]+).*?,\s*(\d+)\s*Hz,\s*([^,]+)", text)
    streams = []
    if video_match:
        codec, pixel_format, width, height, fps = video_match.groups()
        streams.append({"codec_type": "video", "codec_name": codec.strip(), "width": int(width), "height": int(height), "pix_fmt": pixel_format.split("(", 1)[0].strip(), "avg_frame_rate": fps})
    if audio_match:
        codec, sample_rate, layout = audio_match.groups()
        streams.append({"codec_type": "audio", "codec_name": codec.strip(), "sample_rate": sample_rate, "channel_layout": layout.strip(), "profile": "LC" if "aac" in codec else ""})
    return {"format": {"duration": duration}, "streams": streams}


def check_ass(path: Path, width: int, height: int, margin: int, max_chars: int) -> list[str]:
    problems = []
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    positions = re.findall(r"\\pos\((\d+),(\d+)\)", text)
    if not positions:
        problems.append("ASS captions have no explicit positions")
    for x_text, y_text in positions:
        x, y = int(x_text), int(y_text)
        if not (margin <= x <= width - margin and margin <= y <= height - margin):
            problems.append(f"ASS position outside safe zone: {x},{y}")
    for line in text.splitlines():
        if not line.startswith("Dialogue:"):
            continue
        parts = line.split(",", 9)
        if len(parts) < 10:
            problems.append("Malformed ASS dialogue line")
            continue
        visible = re.sub(r"\{[^}]+\}", "", parts[9])
        for caption_line in visible.split(r"\N"):
            if len(caption_line.strip()) > max_chars:
                problems.append(f"ASS caption line exceeds {max_chars} characters")
    return sorted(set(problems))


def main() -> None:
    configure_stdout()
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True, type=Path)
    parser.add_argument("--script", required=True, type=Path)
    parser.add_argument("--srt", required=True, type=Path)
    parser.add_argument("--ass", required=True, type=Path)
    parser.add_argument("--duration", type=float, default=30.0)
    parser.add_argument("--duration-tolerance", type=float, default=0.5)
    parser.add_argument("--width", type=int, default=1080)
    parser.add_argument("--height", type=int, default=1920)
    parser.add_argument("--fps", type=float, default=30.0)
    parser.add_argument("--safe-margin", type=int, default=70)
    parser.add_argument("--max-caption-chars", type=int, default=32)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--ffmpeg")
    parser.add_argument("--ffprobe")
    args = parser.parse_args()

    problems: list[str] = []
    ffmpeg = args.ffmpeg or find_ffmpeg()
    ffprobe = args.ffprobe or find_ffprobe(ffmpeg=ffmpeg)
    if not ffmpeg:
        raise SystemExit("FFmpeg not found")
    for path in [args.video, args.script, args.srt, args.ass]:
        if not path.exists():
            problems.append(f"Required file missing: {path}")
    if problems:
        report = {"ok": False, "problems": problems}
        report_path = args.report or args.video.with_name("validation_report.json")
        write_json(report_path, report)
        raise SystemExit(2)

    info = probe_media(args.video, ffprobe, ffmpeg)
    duration = float(info.get("format", {}).get("duration") or 0)
    if abs(duration - args.duration) > args.duration_tolerance:
        problems.append(f"Duration is {duration:.3f}s; expected {args.duration:.3f}s")
    video_stream = next((stream for stream in info.get("streams", []) if stream.get("codec_type") == "video"), None)
    audio_stream = next((stream for stream in info.get("streams", []) if stream.get("codec_type") == "audio"), None)
    if not video_stream:
        problems.append("Video stream missing")
    else:
        if int(video_stream.get("width") or 0) != args.width or int(video_stream.get("height") or 0) != args.height:
            problems.append(f"Resolution is {video_stream.get('width')}x{video_stream.get('height')}")
        if "h264" not in str(video_stream.get("codec_name", "")).casefold():
            problems.append(f"Video codec is {video_stream.get('codec_name')}; expected H.264")
        if str(video_stream.get("pix_fmt", "")) != "yuv420p":
            problems.append(f"Pixel format is {video_stream.get('pix_fmt')}; expected yuv420p")
        measured_rate = rate(str(video_stream.get("avg_frame_rate") or video_stream.get("r_frame_rate") or "0"))
        if abs(measured_rate - args.fps) > 0.2:
            problems.append(f"Frame rate is {measured_rate:.3f}; expected {args.fps:.3f}")
    if not audio_stream:
        problems.append("Audio stream missing")
    else:
        if "aac" not in str(audio_stream.get("codec_name", "")).casefold():
            problems.append(f"Audio codec is {audio_stream.get('codec_name')}; expected AAC")
        profile = str(audio_stream.get("profile", "")).casefold()
        if profile and "lc" not in profile:
            problems.append(f"AAC profile is {audio_stream.get('profile')}; expected LC")
        channels = int(audio_stream.get("channels") or 0)
        layout = str(audio_stream.get("channel_layout", "")).casefold()
        if channels != 2 and "stereo" not in layout:
            problems.append("Audio is not stereo")

    volume = run([ffmpeg, "-hide_banner", "-i", str(args.video), "-af", "volumedetect", "-vn", "-f", "null", os.devnull], check=False)
    volume_match = re.search(r"mean_volume:\s*(-?inf|-?[\d.]+)\s*dB", volume.stderr)
    mean_volume = volume_match.group(1) if volume_match else "unknown"
    if not volume_match or mean_volume == "-inf" or (mean_volume != "unknown" and float(mean_volume) < -55):
        problems.append(f"Audio is silent or too quiet: {mean_volume} dB")

    frame_results = []
    for fraction in (0.1, 0.5, 0.9):
        timestamp = max(0.0, args.duration * fraction)
        frame = run([
            ffmpeg, "-hide_banner", "-ss", f"{timestamp:.3f}", "-i", str(args.video),
            "-frames:v", "1", "-vf", "signalstats,metadata=print", "-f", "null", os.devnull,
        ], check=False)
        values = re.findall(r"lavfi\.signalstats\.YAVG=([\d.]+)", frame.stderr + frame.stdout)
        yavg = float(values[-1]) if values else -1.0
        frame_results.append({"timestamp": timestamp, "yavg": yavg})
        if yavg < 2.0:
            problems.append(f"Frame appears blank at {timestamp:.2f}s")

    script_text = args.script.read_text(encoding="utf-8-sig")
    cues = parse_subtitles(args.srt)
    subtitle_text = " ".join(text for _, _, text in cues)
    if normalized_text(script_text) != normalized_text(subtitle_text):
        problems.append("SRT text does not match the source script")
    problems.extend(check_ass(args.ass, args.width, args.height, args.safe_margin, args.max_caption_chars))

    report = {
        "ok": not problems,
        "video": str(args.video.resolve()),
        "duration": duration,
        "mean_volume_db": mean_volume,
        "frame_samples": frame_results,
        "subtitle_text_match": normalized_text(script_text) == normalized_text(subtitle_text),
        "problems": sorted(set(problems)),
    }
    report_path = args.report or args.video.with_name("validation_report.json")
    write_json(report_path, report)
    print(report_path.read_text(encoding="utf-8"))
    if problems:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
