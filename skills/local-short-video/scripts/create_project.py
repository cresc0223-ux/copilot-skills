#!/usr/bin/env python3
"""Create a portable local short-video project and configuration."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from video_common import configure_stdout, slugify, write_json


def main() -> None:
    configure_stdout()
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--materials", required=True, type=Path)
    parser.add_argument("--topic", required=True)
    parser.add_argument("--video-type", default="showcase")
    parser.add_argument("--language", required=True)
    parser.add_argument("--review-language", default="")
    parser.add_argument("--project-slug")
    parser.add_argument("--duration", type=float, default=30.0)
    parser.add_argument("--width", type=int, default=1080)
    parser.add_argument("--height", type=int, default=1920)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--voice", required=True)
    parser.add_argument("--voice-rate", default="+8%")
    parser.add_argument("--voice-pitch", default="+0Hz")
    parser.add_argument("--subtitle-style", default="pop-yellow")
    parser.add_argument("--ffmpeg", default="")
    parser.add_argument("--ffprobe", default="")
    args = parser.parse_args()

    workspace = args.workspace.expanduser().resolve()
    materials = args.materials.expanduser().resolve()
    slug = args.project_slug or slugify(args.topic)
    output_root = workspace / "outputs"
    project_dir = output_root / f"local-video-{slug}-{int(args.duration)}s"
    project_dir.mkdir(parents=True, exist_ok=True)

    config = {
        "schema_version": 1,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "workspace_root": str(workspace),
        "materials_root": str(materials),
        "output_root": str(output_root),
        "project_dir": str(project_dir),
        "project_slug": slug,
        "topic": args.topic,
        "video_type": args.video_type,
        "language": args.language,
        "review_language": args.review_language,
        "voice": {
            "provider": "edge-tts",
            "name": args.voice,
            "rate": args.voice_rate,
            "pitch": args.voice_pitch,
        },
        "format": {
            "duration": args.duration,
            "width": args.width,
            "height": args.height,
            "fps": args.fps,
        },
        "subtitles": {
            "style": args.subtitle_style,
            "position": "lower",
            "max_chars": 30,
        },
        "audio": {"source_audio": False, "music": None, "sound_effects": False},
        "tools": {"ffmpeg": args.ffmpeg, "ffprobe": args.ffprobe},
        "ledger_dir": str(workspace / ".local-short-video" / "asset_usage"),
    }
    config_file = project_dir / "project_config.json"
    write_json(config_file, config)
    process = project_dir / "process.md"
    if not process.exists():
        process.write_text(
            "# Production Record\n\n"
            f"- Created: {config['created_at']}\n"
            f"- Topic: {args.topic}\n"
            f"- Video type: {args.video_type}\n"
            f"- Materials: {materials}\n"
            f"- Language: {args.language}\n"
            "- Status: configured\n",
            encoding="utf-8",
        )
    print(config_file)


if __name__ == "__main__":
    main()
