"""One-click Tesseract-OCR install, so "faster OCR" isn't a manual chore.

Building Tesseract from source isn't practical to automate (a full C++
toolchain, Leptonica, hours of build time) - but the official pre-built
Windows installer is published as a GitHub release asset by the
tesseract-ocr project (built by UB-Mannheim). This downloads that
installer and runs it silently.

The release version is resolved dynamically via the GitHub API rather
than a hardcoded filename, so this keeps working as new Tesseract
versions ship.

Windows will still show its own UAC elevation prompt (the installer's
manifest requests admin rights to write to Program Files) - that's the
OS's own consent step and happens regardless of the silent install flags,
so the person running the app always gets one explicit "allow this?"
moment even though the installer's own UI is suppressed.
"""

import json
import os
import subprocess
import tempfile
import urllib.request

RELEASES_API = "https://api.github.com/repos/tesseract-ocr/tesseract/releases/latest"
_HEADERS = {"User-Agent": "silkroadonline-vsbot"}


def find_installer_url():
    """Return (url, filename) for the current Windows installer, or (None, None)."""
    req = urllib.request.Request(RELEASES_API, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    for asset in data.get("assets", []):
        name = asset.get("name", "")
        if name.startswith("tesseract-ocr-w64-setup") and name.endswith(".exe"):
            return asset["browser_download_url"], name
    return None, None


def download_and_install(progress_cb=None):
    """Download + silently run the Tesseract installer.

    progress_cb(str), if given, is called with short status lines as this
    goes - meant to be wired to the GUI log. Returns True on apparent
    success, False otherwise (network failure, no matching asset, the
    installer itself failing/being declined at the UAC prompt, ...).
    """
    def report(msg):
        if progress_cb:
            progress_cb(msg)

    report("Tesseract sürümü GitHub'dan sorgulanıyor...")
    try:
        url, filename = find_installer_url()
    except Exception as exc:
        report(f"Sürüm bilgisi alınamadı: {exc}")
        return False
    if not url:
        report("Uygun bir Windows installer'ı bulunamadı.")
        return False

    tmp_path = os.path.join(tempfile.gettempdir(), filename)
    report(f"İndiriliyor: {filename}")
    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=120) as resp, open(tmp_path, "wb") as f:
            f.write(resp.read())
    except Exception as exc:
        report(f"İndirme başarısız: {exc}")
        return False

    report("Kuruluyor (Windows onay isteyebilir - lütfen izin verin)...")
    try:
        result = subprocess.run(
            [tmp_path, "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"],
            timeout=300,
        )
    except Exception as exc:
        report(f"Kurulum başlatılamadı: {exc}")
        return False
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    if result.returncode != 0:
        report(f"Kurulum tamamlanamadı (çıkış kodu {result.returncode}) - Windows onayı reddetmiş olabilirsiniz.")
        return False

    report("Kurulum tamamlandı ✅")
    return True
