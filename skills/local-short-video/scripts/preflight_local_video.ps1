param(
  [Parameter(Mandatory = $true)][string]$Config,
  [string]$Python = "",
  [switch]$SkipTtsProbe
)

$ErrorActionPreference = "Stop"

if (-not $Python) {
  $command = Get-Command python.exe -ErrorAction SilentlyContinue
  if ($command) { $Python = $command.Source }
}
if (-not $Python) {
  $command = Get-Command py.exe -ErrorAction SilentlyContinue
  if ($command) { $Python = $command.Source }
}
if (-not $Python -and $env:USERPROFILE) {
  $runtimeRoot = Join-Path $env:USERPROFILE ".cache\codex-runtimes"
  $candidate = Get-ChildItem -LiteralPath $runtimeRoot -Recurse -Filter python.exe -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -match "dependencies\\python\\python\.exe$" } |
    Select-Object -First 1
  if ($candidate) { $Python = $candidate.FullName }
}
if (-not $Python) {
  throw "Python was not found. Pass -Python with an absolute executable path."
}

$scriptPath = Join-Path $PSScriptRoot "preflight_local_video.py"
$arguments = @($scriptPath, "--config", $Config)
if ($SkipTtsProbe) { $arguments += "--skip-tts-probe" }
& $Python @arguments
exit $LASTEXITCODE

