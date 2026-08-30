"""Optional OCR + fuzzy name matching layer.

Not a hard dependency: most players running a free hunt tool on modest
hardware don't want a multi-hundred-MB ML library forced on them just to
click monsters. If `easyocr` happens to be installed, this module uses it
to read a candidate crop's actual text and fuzzy-match it against the
target monster list - noticeably more precise than pixel matching because
it recognizes the glyphs rather than comparing raw pixels. If it isn't
installed, `is_available()` is False and callers fall back to the color/
template pipeline in detection.py.
"""

_reader = None
_checked = False


def is_available():
    _ensure_engine()
    return _reader is not False and _reader is not None


def _ensure_engine():
    global _reader, _checked
    if _checked:
        return
    _checked = True
    try:
        import easyocr
        _reader = easyocr.Reader(["en"], gpu=False, verbose=False)
    except Exception:
        _reader = False


def read_text(bgr_image) -> str:
    """Best-effort OCR of a small crop. Returns "" if OCR isn't available."""
    _ensure_engine()
    if not _reader:
        return ""
    try:
        results = _reader.readtext(bgr_image, detail=0, paragraph=False)
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
