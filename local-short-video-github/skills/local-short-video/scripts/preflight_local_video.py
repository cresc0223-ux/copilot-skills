#!/usr/bin/env python3
"""Validate paths, media tools, and a real edge-tts audio/timing probe."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from video_common import (
    MEDIA_EXTS,
    config_path,
    configure_stdout,
    find_ffmpeg,
    find_ffprobe,
    load_json,
    run,
    write_json,
)


def main() -> None:
    configure_stdout()
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--skip-tts-probe", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    config_file = args.config.resolve()
    config = load_json(config_file)
    problems: list[str] = []
    details: dict[str, object] = {}

    try:
        materials = config_path(config, "materials_root", config_file)
        output_root = config_path(config, "output_root", config_file)
    except ValueError as exc:
        raise SystemExit(str(exc))

    ffmpeg = find_ffmpeg(config)
    ffprobe = find_ffprobe(config, ffmpeg)
    if not ffmpeg:
        problems.append("FFmpeg was not found. Set tools.ffmpeg or add ffmpeg to PATH.")
    details["ffmpeg"] = ffmpeg
    details["ffprobe"] = ffprobe
    details["python"] = sys.executable

    if not materials.is_dir():
        problems.append(f"Materials root does not exist: {materials}")
        media_count = 0
    else:
        media_count = sum(1 for path in materials.rglob("*") if path.is_file() and path.suffix.lower() in MEDIA_EXTS)
        if media_count == 0:
            problems.append(f"No supported media found under: {materials}")
    details["media_count"] = media_count

    try:
        output_root.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(prefix="local-video-preflight-", dir=output_root, delete=False) as handle:
            handle.write(b"ok")
            probe_path = Path(handle.name)
        probe_path.unlink()
    except OSError as exc:
        problems.append(f"Output root is not writable: {output_root} ({exc})")

    voice = config.get("voice", {})
    provider = voice.get("provider", "edge-tts")
    voice_name = str(voice.get("name") or "")
    details["voice_provider"] = provider
    details["voice_name"] = voice_name
    if provider != "edge-tts":
        problems.append(f"Unsupported automatic timing provider: {provider}")
    elif not voice_name:
        problems.append("voice.name is required")
    else:
        listed = run([sys.executable, "-m", "edge_tts", "--list-voices"], check=False)
        details["edge_tts_list_returncode"] = listed.returncode
        if listed.returncode != 0:
            problems.append("edge-tts could not list voices; install it or enable network access.")
            details["edge_tts_error"] = (listed.stderr or listed.stdout).strip()[-1000:]
        elif voice_name not in listed.stdout:
            problems.append(f"Selected edge-tts voice is unavailable: {voice_name}")
        elif not args.skip_tts_probe:
            with tempfile.TemporaryDirectory(prefix="local-video-tts-") as tmp:
                media = Path(tmp) / "probe.mp3"
                timing = Path(tmp) / "probe.vtt"
                command = [
                    sys.executable,
                    "-m",
                    "edge_tts",
                    "--voice",
                    voice_name,
                    "--text",
                    "Voice and subtitle timing test.",
                    "--write-media",
                    str(media),
                    "--write-subtitles",
                    str(timing),
                ]
                probe = run(command, check=False)
                details["edge_tts_probe_returncode"] = probe.returncode
                if probe.returncode != 0 or not media.exists() or media.stat().st_size < 512:
                    problems.append("edge-tts failed to generate usable probe audio.")
                    details["edge_tts_probe_error"] = (probe.stderr or probe.stdout).strip()[-1000:]
                if not timing.exists() or "-->" not in timing.read_text(encoding="utf-8-sig", errors="replace"):
                    problems.append("edge-tts failed to generate subtitle timing.")

    report = {
        "ok": not problems,
        "config": str(config_file),
        "materials_root": str(materials),
        "output_root": str(output_root),
        "details": details,
        "problems": problems,
    }
    report_path = args.report or config_file.parent / "preflight_report.json"
    write_json(report_path, report)
    print(report_path.read_text(encoding="utf-8"))
    if problems:
        raise SystemExit(2)


if __name__ == "__main__":
    main()

