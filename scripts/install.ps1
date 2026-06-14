# Grand Log local install (Windows). Run: powershell -ExecutionPolicy Bypass -File scripts\install.ps1
$ErrorActionPreference = "Stop"

Set-Location "$PSScriptRoot\..\reel-pipeline"

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Write-Output "WARNING: ffmpeg is not on PATH. Install it:  winget install Gyan.FFmpeg"
}

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
    Write-Output "Created reel-pipeline\.env from the template."
}

Write-Output ""
Write-Output "Next: edit reel-pipeline\.env and add a brain key (free Gemini key at aistudio.google.com)."
Write-Output "Then check your setup:  python -m pipeline.doctor"
Write-Output ""
try { python -m pipeline.doctor } catch { }
