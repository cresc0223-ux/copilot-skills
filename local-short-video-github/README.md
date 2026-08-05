# Local Short Video Skill

A portable Codex skill for creating polished short-form videos from local images and video clips. It supports project configuration, asset selection and usage tracking, multilingual voiceover, timing-derived captions, FFmpeg rendering, contact sheets, and final media validation.

这是一个可移植的 Codex 本地短视频 Skill。它不绑定品牌、行业、语言、盘符或素材目录，适合商品展示、门店宣传、活动、教程、TikTok、Reels 和 Shorts 等场景。

## Features

- Uses local media without fixed workspace paths.
- Scans, classifies, previews, and tracks source asset usage.
- Generates voice audio and WebVTT timing together with `edge-tts`.
- Stops on missing voice, timing, network, or subtitle text mismatch.
- Creates safe-zone SRT and ASS captions in multiple visual styles.
- Renders mobile MP4 with H.264, `yuv420p`, and AAC LC stereo.
- Validates duration, resolution, frame rate, audio level, nonblank frames, and caption integrity.
- Mutes source audio and adds no music or sound effects unless requested.

## Repository Layout

```text
skills/local-short-video/  # Installable Codex skill
tools/validate_package.py  # Offline package validation
install.ps1                # Windows installer
install.sh                 # macOS/Linux installer
requirements.txt           # Optional TTS dependency
```

## Requirements

- Codex with local skill support.
- Python 3.10 or newer.
- FFmpeg available on `PATH` or supplied in each project config.
- `edge-tts` plus network access when generating voiceover.

FFprobe is optional. The skill falls back to FFmpeg metadata parsing.

## Install

### Windows

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

Install to a custom location:

```powershell
.\install.ps1 -Destination "F:\Codex\skills\local-short-video"
```

Install or update the Python TTS dependency at the same time:

```powershell
.\install.ps1 -InstallDependencies
```

### macOS or Linux

```bash
sh ./install.sh
```

Custom destination and optional dependency installation:

```bash
sh ./install.sh /path/to/codex/skills/local-short-video --install-dependencies
```

Restart or reload Codex after installation.

## Use

Invoke the skill and provide a workspace, local material directory, topic, language, and duration:

```text
Use $local-short-video.
Workspace: D:/VideoWorkspace
Materials: D:/VideoMaterials
Create a lively 30-second vertical product showcase in Spanish.
Do not add music or sound effects.
```

The skill creates a project config, contact sheets, source and review scripts, voice audio, VTT/SRT/ASS captions, selected and used asset manifests, a process log, a validation report, and the final mobile MP4.

## Validate

```bash
python tools/validate_package.py
```

The same offline validation runs on GitHub Actions for every push and pull request.

## Privacy

Source media stays local unless the user explicitly approves an external service. `edge-tts` requires network access and sends the final narration text to Microsoft's speech service.

## License

MIT. See [LICENSE](LICENSE).
