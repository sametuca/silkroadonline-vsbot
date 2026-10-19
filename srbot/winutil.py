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
kernel32 = ctypes.windll.kernel32
shcore = getattr(ctypes.windll, "shcore", None)

# Correct signatures for the calls bring_window_to_front() relies on -
# ctypes otherwise assumes 32-bit int returns, which happens to work most
# of the time for HWNDs but is wrong on 64-bit Windows and has bitten real
# programs before; worth being exact here since a wrong HWND silently
# targets the wrong window instead of erroring.
user32.GetForegroundWindow.restype = wintypes.HWND
user32.GetWindowThreadProcessId.restype = wintypes.DWORD
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.AttachThreadInput.restype = wintypes.BOOL
user32.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.BOOL]
kernel32.GetCurrentThreadId.restype = wintypes.DWORD


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


def _nudge_input_state():
    """Tap Alt (no visible effect) right before SetForegroundWindow.

    Windows' anti focus-stealing protection only allows a process to steal
    foreground if it "recently received input" (among a few other
    exemptions - see SetForegroundWindow's docs). A synthetic key event
    satisfies that check; this is a long-standing, widely used workaround,
    not a hack specific to this app.
    """
    VK_MENU = 0x12
    KEYEVENTF_KEYUP = 0x0002
    try:
        user32.keybd_event(VK_MENU, 0, 0, 0)
        user32.keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, 0)
    except Exception:
        pass


def bring_window_to_front(hwnd):
    """Force `hwnd` to the foreground, working around Windows' focus-
    stealing prevention rather than just calling SetForegroundWindow and
    hoping. That single call is routinely refused for a background
    process - happens regardless of admin/elevation, so running as
    Administrator alone doesn't fix it (elevation and "am I allowed to
    steal focus right now" are unrelated checks).

    The reliable combination: temporarily attach this thread's input
    state to the current foreground window's thread (this is what makes
    Windows treat our SetForegroundWindow call as if it came from the
    already-focused thread, which is always allowed), plus a synthetic
    key tap as a second, independent nudge. Returns True only if the
    window actually became foreground - callers that depend on this for
    input to land should check the return value, not just call and hope.
    """
    try:
        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE

        foreground_hwnd = user32.GetForegroundWindow()
        current_thread_id = kernel32.GetCurrentThreadId()
        target_thread_id = user32.GetWindowThreadProcessId(hwnd, None)
        foreground_thread_id = (
            user32.GetWindowThreadProcessId(foreground_hwnd, None) if foreground_hwnd else 0
        )

        attached_fg = attached_target = False
        if foreground_thread_id and foreground_thread_id != current_thread_id:
            attached_fg = bool(user32.AttachThreadInput(current_thread_id, foreground_thread_id, True))
        if target_thread_id and target_thread_id != current_thread_id:
            attached_target = bool(user32.AttachThreadInput(current_thread_id, target_thread_id, True))

        _nudge_input_state()
        user32.BringWindowToTop(hwnd)
        user32.SetForegroundWindow(hwnd)

        if attached_fg:
            user32.AttachThreadInput(current_thread_id, foreground_thread_id, False)
        if attached_target:
            user32.AttachThreadInput(current_thread_id, target_thread_id, False)
    except Exception:
        pass
    return is_foreground(hwnd)


def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_as_admin(extra_args=()):
    """Re-launch the current program elevated (UAC prompt). True only if Windows started it.

    Needed because the game usually runs elevated: Windows (UIPI) silently blocks a
    non-elevated process's SendInput/SetForegroundWindow calls against it, with no
    error - exactly the "nothing happens" symptom. Returns False when the user
    declines the UAC prompt.
    """
    try:
        args = [a for a in sys.argv[1:] if a != "--elevated"] + list(extra_args)
        if getattr(sys, "frozen", False):
            exe, params = sys.executable, subprocess_list2cmdline(args)
        else:
            exe, params = sys.executable, subprocess_list2cmdline([os.path.abspath(sys.argv[0])] + args)
        result = ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, params, None, 1)
        return result > 32  # <= 32 is an error code (e.g. 5 = the user declined)
    except Exception:
        return False


def subprocess_list2cmdline(args):
    import subprocess
    return subprocess.list2cmdline(args)


def grab_screen(bbox):
    """bbox = (left, top, right, bottom) in absolute screen pixels."""
    if ImageGrab is None:
        raise RuntimeError("Pillow (PIL) is not installed")
    return ImageGrab.grab(bbox=bbox)


def window_pid(hwnd):
    pid = wintypes.DWORD(0)
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value


def is_process_elevated(pid):
    """True/False for the process's elevation, None if it can't be determined."""
    advapi32 = ctypes.windll.advapi32
    kernel32.OpenProcess.restype = wintypes.HANDLE
    handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not handle:
        return None
    token = wintypes.HANDLE()
    try:
        # A non-elevated caller is refused a token of an elevated process; that refusal
        # itself means "elevated" (access denied), anything else is unknown.
        if not advapi32.OpenProcessToken(handle, 0x0008, ctypes.byref(token)):  # TOKEN_QUERY
            return True if kernel32.GetLastError() == 5 else None
        elevation, returned = wintypes.DWORD(), wintypes.DWORD()
        if not advapi32.GetTokenInformation(token, 20, ctypes.byref(elevation), 4, ctypes.byref(returned)):
            return None
        return bool(elevation.value)
    finally:
        if token:
            kernel32.CloseHandle(token)
        kernel32.CloseHandle(handle)


def needs_admin_for(hwnd):
    """True when the game window is elevated and we are not.

    Windows (UIPI) then silently drops every key and click we send, with no
    error - the classic "it finds monsters but never presses anything".
    """
    return not is_admin() and is_process_elevated(window_pid(hwnd)) is True


def character_name_from_title(title):
    """Titles look like '[Murkrow] Destiny Online' - the bracket holds the character name."""
    start, end = title.find("["), title.find("]")
    return title[start + 1:end].strip() if 0 <= start < end else ""


def window_rect(child_hwnd):
    """Outer rectangle (left, top, right, bottom) of the top-level window that owns a Tk widget handle."""
    hwnd = user32.GetAncestor(child_hwnd, 2)  # GA_ROOT: Tk's winfo_id() is an inner child window
    rect = wintypes.RECT()
    if hwnd and user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return rect.left, rect.top, rect.right, rect.bottom
    return None


def make_click_through(child_hwnd):
    """Turn a Tk window into a see-through overlay: mouse input passes through, it never takes focus."""
    GWL_EXSTYLE = -20
    WS_EX_LAYERED, WS_EX_TRANSPARENT, WS_EX_TOOLWINDOW, WS_EX_NOACTIVATE = 0x80000, 0x20, 0x80, 0x08000000
    get = user32.GetWindowLongPtrW
    set_ = user32.SetWindowLongPtrW
    get.restype = ctypes.c_ssize_t
    get.argtypes = [wintypes.HWND, ctypes.c_int]
    set_.restype = ctypes.c_ssize_t
    set_.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]
    hwnd = user32.GetAncestor(child_hwnd, 2)  # GA_ROOT
    style = get(hwnd, GWL_EXSTYLE)
    set_(hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE)
    return hwnd


def is_minimized(hwnd):
    return bool(user32.IsIconic(hwnd))
