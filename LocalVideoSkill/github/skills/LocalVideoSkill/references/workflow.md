# Primer Mall Local Video Workflow Reference

## Directory Pattern

Default workspace after the 4TB drive migration:

```text
workspace_root = F:\PrimerMall_Workspace
materials_root = F:\PrimerMall_Workspace\素材
outputs_root = F:\PrimerMall_Workspace\outputs
logs_root = F:\PrimerMall_Workspace\logs
indexes_root = F:\PrimerMall_Workspace\indexes
```

Use the F-drive material root for future work. The Desktop material folder was deleted after verification and should not be treated as an available backup.

Use a task-specific output folder such as:

```text
outputs/primer-mall-<topic>-30s/
```

Suggested subfolders/files:

```text
voice-candidates/
  candidate_06_valentina_clean.mp3
  candidate_06_valentina_clean.srt
  selected_voice.md
base_no_audio.mp4
subtitles_<voice>_pop_lower.ass
final_<voice>_mobile_aac.mp4
preview_<voice>_contact_sheet.jpg
storyboard_*.md
used_assets_*.json
used_assets_*.csv
```

## Asset Scope Decision

Always decide the scope before selecting footage:

```text
single_store:
  source = F:\PrimerMall_Workspace\素材\单店\<store-folder>
  use only that store's assets unless the user explicitly approves supplements

overall_brand:
  source = F:\PrimerMall_Workspace\素材\00_素材库_已整理
  use any suitable material from the organized general library
```

Treat requests mentioning a branch, address, city, or exact store folder as `single_store`. Treat requests for Primer Mall as a whole, storewide assortment, category promos, or generic brand clips as `overall_brand`.

Known single-store root:

```text
F:\PrimerMall_Workspace\素材\单店
```

If a requested store folder is empty or lacks enough footage, say so and ask whether to supplement from the general library. Do not silently mix unrelated store folders.

## Script Rules

- Match each spoken line to visible product footage.
- Prefer short, lively retail phrasing over stiff corporate copy.
- Keep Spanish copy natural for broad Latin American audiences.
- Mention `Primer Mall` only where it helps branding.
- Avoid mentioning Chile, TikTok, platform targeting, or internal context unless explicitly requested.
- Provide Chinese translation when the user needs to review meaning.

## Voice Rules

Default voice:

```text
voice: es-UY-ValentinaNeural
rate: around +13%
pitch: around +11Hz
style: clean, stable, positive, less AI-like
```

If the user asks for more options, generate multiple MP3 candidates and a manifest with voice, rate, pitch, duration, and subjective Chinese notes.

## Caption Rules

Use lower-third pop captions:

```text
Font: Arial or available bold sans
Size: about 82-86 at 1080x1920
Position: \pos(540,1425)
Fill: yellow
Inner outline: orange
Outer rim: white
Glow: yellow
Animation: none
```

Timing should follow voiceover SRT closely. Avoid delayed captions. Prefer short caption blocks of one or two lines.

Review punctuation before final render. Some TTS-generated SRT files omit Spanish opening marks like `¿` even when the script contains them.

## Render Rules

Base render:

```powershell
ffmpeg -i base_no_audio.mp4 -i voice.mp3 -filter_complex "[0:v]ass='subtitles.ass'[v];[1:a]apad=whole_dur=30[a]" -map "[v]" -map "[a]" -t 30 ...
```

Phone-facing final:

```powershell
ffmpeg -i captioned_video.mp4 -i selected_voice.mp3 -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 320k -ar 48000 -ac 2 -t 30 -movflags +faststart final_mobile_aac.mp4
```

Do not ship MP4-with-MP3 to phones as the primary final, even if desktop playback works.

## Verification Checklist

- `ffprobe` shows `1080x1920`, `30fps`, expected duration.
- Audio codec is AAC LC stereo for phone final.
- Source audio is muted unless requested.
- Captions are readable, low enough, and not cut off.
- Contact sheet has no black/blank frames except intentional tail space.
- `process.md` records inputs, voice, subtitles, render command intent, output path, and phone copy path if applicable.
- For single-store videos, `process.md`, storyboard, and used-asset manifests record the chosen `store_folder`.
