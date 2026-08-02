---
name: primer-mall-local-video
description: Local short-video production workflow for Primer Mall or similar retail promo videos. Use when creating or revising local TikTok/Reels-style product videos from desktop assets, especially Spanish voiceover, muted source clips, yellow pop captions, ffmpeg rendering, process.md logging, desktop delivery, and mobile-compatible MP4/AAC exports.
---

# Primer Mall Local Video

## Overview

Create local retail promo videos from user-provided assets. Keep the workflow local-first, produce Spanish short-video voiceovers, burn in bold lower-third captions, verify playback, and keep a running `process.md`.

## Defaults

- Brand: `Primer Mall`, unless the user changes it.
- Current workspace root: `F:\PrimerMall_Workspace`.
- Preferred material root after the 4TB drive migration: `F:\PrimerMall_Workspace\素材`.
- Main language: Spanish for voiceover and captions; provide Chinese translation when the user needs to review the script.
- Default voice: candidate 06, `es-UY-ValentinaNeural`, described as clean, stable, and relatively less AI-like.
- Default format: vertical `9:16`, `1080x1920`, `30fps`, `30s` unless overridden.
- Audio policy: mute all source-asset audio; no BGM unless explicitly requested.
- Export policy: for phones or TikTok, output MP4 with H.264 video and AAC LC stereo audio. Do not deliver MP4-with-MP3 as the phone-facing final.
- Captions: large yellow pop text, orange stroke, white rim, glow, no fade/word animation, placed low in the lower third.
- Caption fidelity: do not summarize, shorten, or rewrite spoken captions. If a spoken line is too long, split it into consecutive caption events that preserve every spoken word, follow the voice timing, and stay inside the visible frame.
- Logging: update the project `process.md` after each meaningful step.

## Asset Scope Rule

- For future Primer Mall work, look under `F:\PrimerMall_Workspace\素材` first. Keep outputs, logs, indexes, temp files, and tool caches under sibling folders in `F:\PrimerMall_Workspace` unless the user requests Desktop delivery.
- For a single-store video, use only the matching store folder under `F:\PrimerMall_Workspace\素材\单店\<store-folder>` unless the user explicitly allows supplementing from the general library.
- For an overall Primer Mall brand/storewide video, freely use the general asset library under `F:\PrimerMall_Workspace\素材\00_素材库_已整理`.
- Treat `F:\PrimerMall_Workspace\素材\00_素材库_已整理\90_待识别_xin` as a low-frequency backup pool only. Prefer clear main categories first; use this pool sparingly for toys, charms, jewelry, plush, or special filler shots when the theme needs them.
- Before editing, classify the request as `single_store` or `overall_brand`. If the request names a location/address/store folder, treat it as `single_store`.
- Do not mix another store's folder into a single-store video. If the matching store folder is empty or weak, report that and ask whether to supplement from the general library.

## Workflow

1. Locate the current output folder and `process.md`. If none exists, create an output folder under `outputs/` and start `process.md`.
2. Decide the asset scope: `single_store` uses only the matching folder in `素材\单店`; `overall_brand` uses `素材\00_素材库_已整理`.
3. Inspect local assets with `ffprobe` and visual contact sheets. Use only local files unless the user explicitly approves online sources or paid generation.
4. Design a concise Spanish script around the exact visible products. Do not mention Chile, TikTok, or user background unless the user explicitly asks; only use the brand name when appropriate.
5. Generate or reuse voiceover with `edge-tts`. Prefer `es-UY-ValentinaNeural` for this user after the 06 selection. Save the audio, raw SRT, and script text.
6. Convert the voiceover SRT to ASS captions with `scripts/create_pop_ass.py`. Keep caption text synchronized to the spoken segments; split long lines into short two-line blocks.
7. Render the muted video with burned-in captions and the selected voice. Use `ffmpeg`; preserve a clean base video without source audio when useful.
8. Export the phone-facing final with AAC LC stereo using `scripts/remux_mobile_aac.ps1` or equivalent ffmpeg settings.
9. Verify with `ffprobe`: duration, resolution, fps, video codec, audio codec/profile/channels. Generate a contact sheet and inspect subtitle position/readability.
10. If the user asks to download, copy the chosen final video to Desktop with a clear versioned Chinese filename.
11. Record every completed action in `process.md`, including request type, asset scope, selected store folder if any, selected voice, output files, codec decisions, and compatibility fixes.

## Practical Notes

- If a video sounds different from the standalone voice candidate, check whether the audio was re-encoded. MP3 copied into MP4 may match the candidate but can fail on phones; AAC is the safer final.
- If the user wants "the same voice" and also phone playback, use high-bitrate AAC LC stereo and explain the small tradeoff.
- Review auto-generated SRT text before final render. Edge TTS can omit Spanish opening punctuation such as `¿`.
- Use the selected voice record if present, e.g. `voice-candidates/selected_voice.md`.
- Keep final deliverables under `outputs/`; copy to Desktop only on request.
- Keep single-store source attribution explicit in storyboards and used-asset manifests, including `store_folder`.

## Resources

- `scripts/create_pop_ass.py`: Convert an SRT file into the yellow pop ASS caption style.
- `scripts/remux_mobile_aac.ps1`: Replace or add a phone-compatible AAC LC stereo audio track while copying the video stream.
- `references/workflow.md`: Detailed local workflow defaults, naming conventions, and troubleshooting checklist.
