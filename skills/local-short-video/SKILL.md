---
name: local-short-video
description: Create, revise, and validate short-form videos from local image and video libraries. Use for TikTok, Reels, Shorts, product, store, event, tutorial, showcase, or general promotional edits that need portable workspace configuration, asset scanning and usage tracking, script writing, multilingual TTS voiceover, timing-derived subtitles, FFmpeg rendering, contact sheets, process logs, and mobile-compatible H.264/AAC MP4 delivery.
---

# Local Short Video

Build a complete short-video project from user-owned local media without assuming a brand, industry, language, drive letter, or folder layout.

## Required Inputs

Determine these values before production:

- `workspace_root`: durable project and ledger location.
- `materials_root`: local source images and videos.
- `topic` and `video_type`: what the video should communicate.
- `language`: spoken language; ask only when it cannot be inferred.
- `duration` and aspect ratio; default to 30 seconds and vertical 9:16.
- Voice preference, brand rules, mandatory claims, and prohibited content when provided.

Never invent a fixed path. If a required root is unknown, ask for it once, save it in `project_config.json`, and reuse it for the project.

## Non-Negotiables

- Use local source media unless the user approves external media or generation.
- Inspect a contact sheet before finalizing claims or the script. Make every factual claim supportable by visible media or user-provided facts.
- Generate TTS audio and subtitle timing in the same operation. Do not estimate subtitle timing from the script.
- Stop on missing TTS, unavailable voice, network failure, empty audio, missing timing file, or script/subtitle text mismatch. Never present a silent export as voiced completion.
- Preserve the spoken text in captions. Split display blocks without summarizing, translating, or dropping words.
- Mute source clips by default. Add music, source audio, or sound effects only when requested.
- Export MP4 with H.264, `yuv420p`, AAC LC stereo, fast start, requested dimensions, and requested frame rate.
- Run final validation and fix failures before delivery.
- Deliver the final script in the spoken language and a review translation when requested or useful.
- Record only assets that appear in the final edit; update the persistent usage ledger after successful validation.

## Workflow

1. Read [workflow.md](references/workflow.md). Read [copywriting-voice.md](references/copywriting-voice.md) before scripting and voice selection, and [editing-subtitles.md](references/editing-subtitles.md) before rendering.
2. Run `scripts/create_project.py` to create the project folder and `project_config.json`.
3. Run `scripts/preflight_local_video.ps1` or `scripts/preflight_local_video.py`. Treat any nonzero exit as blocking.
4. Run `scripts/select_assets.py`, create `used_assets_candidates.json`, and generate a preview with `scripts/create_contact_sheet.py`.
5. Inspect the preview. Write the final source-language script and review translation. Keep the script within the voice duration budget.
6. Use `scripts/audition_voices.py` when the voice is unspecified or quality-sensitive. Save the chosen voice settings.
7. Run `scripts/synthesize_voice.py` to create voice audio plus VTT. Normalize VTT to SRT with `scripts/normalize_subtitles.py`.
8. Generate ASS captions with `scripts/create_pop_ass.py`. Choose a style appropriate to the subject; keep captions in the safe zone.
9. Render with `scripts/render_local_video.py`. It creates a muted visual base, burns captions, normalizes voice loudness, exports a mobile MP4, and writes actual asset usage.
10. Run `scripts/validate_final.py` with the video, SRT, ASS, and script. Do not deliver if validation fails.
11. Run `scripts/update_asset_usage.py`, finish `process.md`, and deliver the MP4, contact sheet, scripts, and validation report.

## Failure Policy

- Ask for permission before installing software, downloading models, or using network services.
- If `edge-tts` cannot generate both audio and VTT, stop and report the exact failed check.
- If selected media cannot support the requested message, show the contact sheet and request more material or approval to narrow the script.
- If voice duration exceeds the target, revise the script or voice rate and regenerate audio and timing together.
- If subtitle text differs from the spoken script, regenerate from the source script; do not hand-edit timing around a mismatch.

## Project Output

Each project folder must contain:

- `project_config.json`, `process.md`
- `script_source.txt` and, when applicable, `script_review.txt`
- `selected_assets.json`, `used_assets.json`, `used_assets.csv`
- `preview_assets_contact_sheet.jpg`, `preview_final_contact_sheet.jpg`
- voice audio, raw VTT, normalized SRT, and final ASS
- `validation_report.json`
- `final_<project>_mobile.mp4`

Keep all project paths relative to roots stored in the config where practical. Never embed machine-specific paths in this Skill.
