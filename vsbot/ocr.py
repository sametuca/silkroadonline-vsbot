"""Optional OCR + fuzzy name matching layer.

Two possible backends, tried in this order:

  1. **Tesseract** (via `pytesseract`) - a small, fast, non-ML OCR engine.
     Only usable if the separate `tesseract.exe` binary is installed and
     found on PATH (or in its default install location) - there is no
     reliable portable/bundleable Windows build of it, so this stays a
     "use it if you have it" install, documented in the README. On the
     tiny crops this module actually feeds it (a single name-plate, not a
     full screen), it typically runs in a few milliseconds - fast enough
     to run every scan cycle.
  2. **easyocr** - a deep-learning OCR engine. Much slower per call
     (hundreds of ms, no GPU assumed) but pure-Python/pip-installable
     with no separate binary, so it's the fallback for anyone who'd
     rather not install Tesseract separately.

Neither is a hard dependency: if neither is available, `is_available()`
is False and callers fall back to the color/template pipeline instead.
"""

import os

_engine = None  # "tesseract" | "easyocr" | False (checked, unavailable) | None (not checked yet)
_easyocr_reader = None

_TESSERACT_FALLBACK_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
]


def is_available():
    _ensure_engine()
    return _engine is not False


def engine_name():
    """'tesseract', 'easyocr', or None if OCR isn't available - for the GUI to show which one is active."""
    _ensure_engine()
    return _engine or None


def reset_cache():
    """Forget the cached engine choice so the next call re-probes for
    Tesseract - call this right after installing it (tesseract_installer)
    so the app notices without needing a restart."""
    global _engine
    _engine = None


def _ensure_engine():
    global _engine
    if _engine is not None:
        return
    _engine = _try_tesseract() or _try_easyocr() or False


def _try_tesseract():
    try:
        import pytesseract
    except ImportError:
        return None
    try:
        pytesseract.get_tesseract_version()
        return "tesseract"
    except Exception:
        pass
    for candidate in _TESSERACT_FALLBACK_PATHS:
        if os.path.isfile(candidate):
            pytesseract.pytesseract.tesseract_cmd = candidate
            try:
                pytesseract.get_tesseract_version()
                return "tesseract"
            except Exception:
                continue
    return None


def _try_easyocr():
    global _easyocr_reader
    try:
        import easyocr
        _easyocr_reader = easyocr.Reader(["en"], gpu=False, verbose=False)
        return "easyocr"
    except Exception:
        return None


def read_text(bgr_image) -> str:
    """Best-effort OCR of a small crop. Returns "" if OCR isn't available."""
    _ensure_engine()
    if _engine == "tesseract":
        return _read_tesseract(bgr_image)
    if _engine == "easyocr":
        return _read_easyocr(bgr_image)
    return ""


def _read_tesseract(bgr_image) -> str:
    try:
        import pytesseract
        from PIL import Image
        rgb = bgr_image[:, :, ::-1]
        img = Image.fromarray(rgb)
        # --psm 7: treat the crop as a single line of text (it is one) -
        # much faster and more accurate than the default full-page mode.
        text = pytesseract.image_to_string(img, config="--psm 7")
        return text.strip()
    except Exception:
        return ""


def _read_easyocr(bgr_image) -> str:
    if _easyocr_reader is None:
        return ""
    try:
        results = _easyocr_reader.readtext(bgr_image, detail=0, paragraph=False)
        return " ".join(results).strip()
    except Exception:
        return ""


def fuzzy_match(text, candidates, min_score=70):
    """Return (best_candidate, score 0-100) or (None, score) if below min_score."""
    if not text or not candidates:
        return None, 0

    text_low = text.lower()
    try:
        from rapidfuzz import fuzz
        scored = [(c, fuzz.partial_ratio(text_low, c.lower())) for c in candidates]
    except ImportError:
        import difflib
        scored = [(c, difflib.SequenceMatcher(None, text_low, c.lower()).ratio() * 100) for c in candidates]

    best_candidate, best_score = max(scored, key=lambda pair: pair[1])
    if best_score >= min_score:
        return best_candidate, best_score
    return None, best_score
