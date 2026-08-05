#!/usr/bin/env python3
"""Shared helpers for the local-short-video scripts."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".mkv", ".avi", ".webm"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
MEDIA_EXTS = VIDEO_EXTS | IMAGE_EXTS


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def resolve_path(value: str | Path, base: Path) -> Path:
    path = Path(os.path.expandvars(str(value))).expanduser()
    if not path.is_absolute():
        path = base / path
    return path.resolve()


def config_path(config: dict[str, Any], key: str, config_file: Path, default: str | None = None) -> Path:
    raw = config.get(key, default)
    if not raw:
        raise ValueError(f"Missing required config field: {key}")
    return resolve_path(str(raw), config_file.parent)


def find_executable(explicit: str | None, names: list[str]) -> str | None:
    if explicit:
        expanded = Path(os.path.expandvars(explicit)).expanduser()
        if expanded.exists():
            return str(expanded.resolve())
    for name in names:
        found = shutil.which(name)
        if found:
            return found
    return None


def find_ffmpeg(config: dict[str, Any] | None = None) -> str | None:
    tools = (config or {}).get("tools", {})
    return find_executable(tools.get("ffmpeg"), ["ffmpeg.exe", "ffmpeg"])


def find_ffprobe(config: dict[str, Any] | None = None, ffmpeg: str | None = None) -> str | None:
    tools = (config or {}).get("tools", {})
    found = find_executable(tools.get("ffprobe"), ["ffprobe.exe", "ffprobe"])
    if found:
        return found
    if ffmpeg:
        sibling = Path(ffmpeg).with_name("ffprobe" + Path(ffmpeg).suffix)
        if sibling.exists():
            return str(sibling)
    return None


def run(command: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="replace",
    )


def probe_media(path: Path, ffprobe: str | None, ffmpeg: str | None = None) -> dict[str, Any]:
    if ffprobe:
        proc = run(
            [ffprobe, "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
            check=False,
        )
        if proc.returncode == 0:
            try:
                return json.loads(proc.stdout)
            except json.JSONDecodeError:
                pass
    if not ffmpeg:
        return {}
    proc = run([ffmpeg, "-hide_banner", "-i", str(path)], check=False)
    text = proc.stderr
    duration_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", text)
    duration = 0.0
    if duration_match:
        hours, minutes, seconds = duration_match.groups()
        duration = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    streams: list[dict[str, Any]] = []
    video_line_match = re.search(r"^.*Video:\s*.*$", text, re.MULTILINE)
    if video_line_match:
        video_line = video_line_match.group(0)
        codec_match = re.search(r"Video:\s*([^\s,(]+)", video_line)
        format_match = re.search(r",\s*([a-zA-Z0-9_]+)(?:\([^)]*\))?,\s*(\d+)x(\d+)", video_line)
        fps_match = re.search(r",\s*([\d.]+)\s*fps", video_line)
    else:
        codec_match = format_match = fps_match = None
    if codec_match and format_match and fps_match:
        pixel_format, width, height = format_match.groups()
        streams.append({
            "codec_type": "video",
            "codec_name": codec_match.group(1).strip(),
            "pix_fmt": pixel_format.strip(),
            "width": int(width),
            "height": int(height),
            "avg_frame_rate": fps_match.group(1),
        })
    audio_match = re.search(r"Audio:\s*([^,\n]+).*?,\s*(\d+)\s*Hz,\s*([^,\n]+)", text)
    if audio_match:
        codec, sample_rate, layout = audio_match.groups()
        streams.append({
            "codec_type": "audio",
            "codec_name": codec.strip().split(" ", 1)[0],
            "sample_rate": sample_rate,
            "channel_layout": layout.strip().split(",", 1)[0],
            "profile": "LC" if "(LC)" in codec else "",
        })
    return {"format": {"duration": duration}, "streams": streams}


def media_summary(path: Path, ffprobe: str | None, ffmpeg: str | None = None) -> dict[str, Any]:
    info = probe_media(path, ffprobe, ffmpeg)
    video = next((item for item in info.get("streams", []) if item.get("codec_type") == "video"), {})
    duration = info.get("format", {}).get("duration") or video.get("duration") or 0
    try:
        duration_value = round(float(duration), 3)
    except (TypeError, ValueError):
        duration_value = 0.0
    return {
        "duration": duration_value,
        "width": int(video.get("width") or 0),
        "height": int(video.get("height") or 0),
        "codec": str(video.get("codec_name") or ""),
        "has_audio": any(item.get("codec_type") == "audio" for item in info.get("streams", [])),
        "probe_error": info.get("probe_error", ""),
    }


def normalized_text(value: str) -> str:
    return "".join(char.casefold() for char in value if char.isalnum())


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    return value or "video-project"


def configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
