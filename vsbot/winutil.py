"""Windows helpers: DPI awareness, window enumeration, and screen capture.

Capture is done with PIL.ImageGrab against absolute screen coordinates - the
bot only ever looks at pixels that are already on screen, the same as a
human would see them. No process handles are opened for reading/writing
memory.
"""

import ctypes
import ctypes.wintypes as wintypes
import os
import sys

try:
    from PIL import ImageGrab
except ImportError:  # pillow not installed yet; surfaced clearly at runtime
    ImageGrab = None

user32 = ctypes.windll.user32
shcore = getattr(ctypes.windll, "shcore", None)


def try_set_process_dpi_aware():
    """Make coordinates match real screen pixels instead of DPI-scaled ones."""
    try:
        if shcore is not None:
            # PROCESS_PER_MONITOR_DPI_AWARE
            shcore.SetProcessDpiAwareness(2)
            return
    except Exception:
        pass
    try:
        user32.SetProcessDPIAware()
    except Exception:
        pass


def enumerate_top_level_windows(min_w=200, min_h=200):
    """Return a list of (hwnd, title, (left, top, right, bottom)) for visible windows."""
    results = []

    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

    def _cb(hwnd, _lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            return True
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        title = buf.value
        if not title.strip():
            return True
        rect = wintypes.RECT()
        if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            return True
        w = rect.right - rect.left
        h = rect.bottom - rect.top
        if w < min_w or h < min_h:
            return True
        results.append((hwnd, title, (rect.left, rect.top, rect.right, rect.bottom)))
        return True

    user32.EnumWindows(EnumWindowsProc(_cb), 0)
    return results


def get_window_client_rect_on_screen(hwnd):
    """Return (left, top, right, bottom) of a window's client area in screen coords."""
    client_rect = wintypes.RECT()
    if not user32.GetClientRect(hwnd, ctypes.byref(client_rect)):
        return None
    top_left = wintypes.POINT(0, 0)
    user32.ClientToScreen(hwnd, ctypes.byref(top_left))
    left = top_left.x
    top = top_left.y
    right = left + (client_rect.right - client_rect.left)
    bottom = top + (client_rect.bottom - client_rect.top)
    return left, top, right, bottom


def is_window_valid(hwnd):
    return bool(user32.IsWindow(hwnd))


def is_foreground(hwnd):
    """True if `hwnd` is currently the OS-focused window.

    SendInput always delivers keystrokes to whatever window has focus, not
    to a chosen target - so anything that presses keys needs to check this
    (and refocus if not) right before pressing, or clicks elsewhere by the
    user will silently steal all subsequent input.
    """
    try:
        return user32.GetForegroundWindow() == hwnd
    except Exception:
        return False


def bring_window_to_front(hwnd):
    """Best-effort focus request. Returns True only if the window actually
    became the foreground window - Windows can silently refuse
    SetForegroundWindow (the "foreground lock" restriction, or a window
    running at higher process integrity than us, e.g. a game launched as
    Administrator while we aren't) so callers that depend on this for
    input to land should check the return value, not just call and hope.
    """
    try:
        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        user32.SetForegroundWindow(hwnd)
    except Exception:
        pass
    return is_foreground(hwnd)


def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_as_admin():
    """Re-launch the current process elevated (UAC prompt) and exit this one.

    Needed when the game itself runs elevated (common with anti-cheat
    launchers) - Windows' UIPI silently blocks a non-elevated process's
    SendInput/SetForegroundWindow calls against a higher-integrity window,
    with no error, which is exactly the "nothing happens" symptom this
    fixes.
    """
    try:
        if getattr(sys, "frozen", False):
            exe, params = sys.executable, ""
        else:
            exe, params = sys.executable, f'"{os.path.abspath(sys.argv[0])}"'
        ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, params, None, 1)
        return True
    except Exception:
        return False


def grab_screen(bbox):
    """bbox = (left, top, right, bottom) in absolute screen pixels."""
    if ImageGrab is None:
        raise RuntimeError("Pillow (PIL) is not installed")
    return ImageGrab.grab(bbox=bbox)
