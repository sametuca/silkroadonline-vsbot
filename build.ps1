# Builds a single-file Windows executable (dist\SilkroadVisionBot.exe).
# Same command the GitHub Actions release workflow runs - use this to test
# a build locally before tagging a release.

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

pyinstaller --noconfirm --onefile --windowed --name SilkroadVisionBot --add-data "assets;assets" main.py

Write-Host ""
Write-Host "Done: dist\SilkroadVisionBot.exe" -ForegroundColor Green
