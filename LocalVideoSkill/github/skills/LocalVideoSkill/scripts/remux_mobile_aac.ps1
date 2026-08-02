param(
  [Parameter(Mandatory=$true)][string]$Video,
  [Parameter(Mandatory=$true)][string]$Audio,
  [Parameter(Mandatory=$true)][string]$Out,
  [string]$FFmpeg = "ffmpeg",
  [double]$Duration = 30,
  [string]$AudioBitrate = "320k"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $Video)) {
  throw "Video not found: $Video"
}
if (-not (Test-Path -LiteralPath $Audio)) {
  throw "Audio not found: $Audio"
}

$outDir = Split-Path -Parent $Out
if ($outDir) {
  New-Item -ItemType Directory -Force -Path $outDir | Out-Null
}

& $FFmpeg -y -hide_banner -loglevel error `
  -i $Video `
  -i $Audio `
  -map 0:v:0 `
  -map 1:a:0 `
  -c:v copy `
  -c:a aac `
  -b:a $AudioBitrate `
  -ar 48000 `
  -ac 2 `
  -t $Duration `
  -movflags +faststart `
  $Out

if ($LASTEXITCODE -ne 0) {
  throw "ffmpeg failed with exit code $LASTEXITCODE"
}

Get-Item -LiteralPath $Out
