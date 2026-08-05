param(
  [string]$Destination = "",
  [switch]$InstallDependencies,
  [string]$Python = ""
)

$ErrorActionPreference = "Stop"
$source = Join-Path $PSScriptRoot "skills\local-short-video"

if (-not (Test-Path -LiteralPath (Join-Path $source "SKILL.md"))) {
  throw "Skill source is incomplete: $source"
}

if (-not $Destination) {
  $codexRoot = $env:CODEX_HOME
  if (-not $codexRoot) {
    if (-not $env:USERPROFILE) { throw "USERPROFILE is unavailable; pass -Destination explicitly." }
    $codexRoot = Join-Path $env:USERPROFILE ".codex"
  }
  $Destination = Join-Path (Join-Path $codexRoot "skills") "local-short-video"
}

$Destination = [System.IO.Path]::GetFullPath($Destination)
$parent = Split-Path -Parent $Destination
New-Item -ItemType Directory -Force -Path $parent | Out-Null

$backup = ""
if (Test-Path -LiteralPath $Destination) {
  $backup = "$Destination.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
  Move-Item -LiteralPath $Destination -Destination $backup
}

try {
  Copy-Item -LiteralPath $source -Destination $Destination -Recurse
} catch {
  if ($backup -and -not (Test-Path -LiteralPath $Destination)) {
    Move-Item -LiteralPath $backup -Destination $Destination
  }
  throw
}

if ($InstallDependencies) {
  if (-not $Python) {
    $command = Get-Command python.exe -ErrorAction SilentlyContinue
    if (-not $command) { $command = Get-Command python3.exe -ErrorAction SilentlyContinue }
    if (-not $command) { $command = Get-Command py.exe -ErrorAction SilentlyContinue }
    if ($command) { $Python = $command.Source }
  }
  if (-not $Python) { throw "Python was not found. Install Python or pass -Python explicitly." }
  & $Python -m pip install -r (Join-Path $PSScriptRoot "requirements.txt")
  if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed with exit code $LASTEXITCODE." }
}

Write-Host "Installed local-short-video to: $Destination"
if ($backup) { Write-Host "Previous installation backed up to: $backup" }
Write-Host "Reload Codex, then invoke `$local-short-video."
