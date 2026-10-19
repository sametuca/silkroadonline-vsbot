# Builds a single-file Windows executable (dist\SilkroadVisionBot.exe) and
# smoke-tests it. The GitHub Actions release workflow does the same steps.

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller

# Training dependencies (torch & co.) are only needed by `python -m srbot.train`;
# keep them out of the exe even when they are installed on this machine.
python -m PyInstaller --noconfirm --onefile --windowed --name SilkroadVisionBot `
    --collect-all rapidocr_onnxruntime --collect-all customtkinter `
    --exclude-module ultralytics --exclude-module torch --exclude-module torchvision `
    --exclude-module onnx --exclude-module matplotlib --exclude-module polars `
    main.py

# Windowed exes have no console: the self-test reports through a file and the exit code.
$result = Join-Path $env:TEMP "svb-selftest.txt"
Remove-Item $result -ErrorAction SilentlyContinue
$proc = Start-Process -FilePath "dist\SilkroadVisionBot.exe" -ArgumentList "--selftest", $result -Wait -PassThru
if ($proc.ExitCode -ne 0) {
    Write-Host (Get-Content $result -Raw -ErrorAction SilentlyContinue) -ForegroundColor Red
    throw "Self-test of the built exe failed (exit code $($proc.ExitCode))."
}

Write-Host ""
Write-Host "Done: dist\SilkroadVisionBot.exe (self-test passed)" -ForegroundColor Green
