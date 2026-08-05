# Portable Production Workflow

## 1. Configure the project

Create one config per video. Absolute roots are accepted on Windows, macOS, and Linux. Relative paths resolve from the config file directory.

Required fields:

```json
{
  "workspace_root": "D:/VideoWorkspace",
  "materials_root": "D:/VideoMaterials",
  "output_root": "D:/VideoWorkspace/outputs",
  "project_slug": "summer-products",
  "topic": "Summer product showcase",
  "video_type": "product_showcase",
  "language": "es-MX",
  "review_language": "zh-CN",
  "voice": {"provider": "edge-tts", "name": "es-MX-DaliaNeural", "rate": "+12%", "pitch": "+8Hz"},
  "format": {"duration": 30, "width": 1080, "height": 1920, "fps": 30},
  "subtitles": {"style": "pop-yellow", "position": "lower", "max_chars": 30},
  "audio": {"source_audio": false, "music": null, "sound_effects": false},
  "tools": {"ffmpeg": "", "ffprobe": ""}
}
```

Do not carry brand-specific fields into another project unless the user repeats them.

## 2. Preflight

Require all of the following before editing:

- Python can run the bundled scripts.
- FFmpeg is available. FFprobe is preferred; FFmpeg probing is the fallback.
- Material root exists and contains supported media.
- Output root can be created and written.
- The selected TTS provider and voice are available.
- A short TTS probe creates nonempty audio and a timing file.

`edge-tts` needs network access. If it is unavailable, report the problem and request permission for the missing installation or connectivity. Do not silently switch voices or providers.

## 3. Inspect and select media

Scan recursively for MP4, MOV, M4V, MKV, AVI, WebM, JPG, JPEG, PNG, and WebP. Exclude output, cache, proxy, thumbnail, and hidden working folders.

Classify files by folder and filename hints into:

- `detail`: product or subject close-ups.
- `context`: wide, shelf, room, aisle, venue, or environment views.
- `location`: facade, entrance, exterior, sign, address, or map views.
- `people`: demonstrations, hands, customers, staff, or portraits.
- `brand`: logos, title cards, packaging, and identity shots.
- `unknown`: useful media without a reliable role.

Prefer a varied role mix and lower historical usage counts. Do not select by file size alone. For requested categories, match folder names and paths before ranking.

Generate a contact sheet and inspect it before scripting. For clips that must reveal a sign, person, action, or product, verify and store a suitable `source_start` instead of taking an arbitrary first second.

## 4. Script and duration budget

Write from the selected media and user-provided facts. Use the structures in `copywriting-voice.md`.

Estimate speech budget before TTS:

- Mandarin: roughly 3.5 to 4.5 characters per second.
- Spanish: roughly 2.2 to 2.8 words per second.
- English: roughly 2.2 to 2.7 words per second.

These are planning ranges, not timing data. TTS output remains the source of truth.

## 5. Voice and timing

List voices for the requested locale and audition two to four suitable candidates when quality matters. Keep samples on the same sentence. Select for clarity, energy, pronunciation, and fit with the audience.

Generate media and VTT together from the final script. Save provider, voice, locale, rate, pitch, command result, and measured duration. If the text changes, regenerate both files.

## 6. Captions and edit

Normalize VTT to UTF-8 SRT. Verify concatenated caption text equals the final script after punctuation and whitespace normalization. Generate ASS only after that check.

Use a visual rhythm suited to the request:

- energetic promo: mostly 1.2 to 2.6 second shots.
- product showcase: mostly 1.8 to 3.2 second shots.
- tutorial or explanation: mostly 2.5 to 5 second shots.

Combine details with context shots. Use restrained crop motion on stills, purposeful source starts on video, and cuts aligned to ideas. Avoid transitions that hide the subject.

## 7. Validate and deliver

Validation must check:

- requested duration, dimensions, and frame rate.
- H.264 and `yuv420p` video.
- AAC LC stereo audio and non-silent level.
- nonblank frames at multiple points.
- SRT text equality with the source script.
- ASS positions and line lengths inside the configured safe area.

Finish `process.md` with the request, roots, selected media, script files, voice settings, subtitle files, render summary, validation result, ledger update, and final paths.
