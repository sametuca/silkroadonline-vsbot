"""Synthetic keyboard/mouse input.

All of this simulates a human at the keyboard/mouse - hardware-level scan
codes through the Windows SendInput API by default, with pydirectinput and
the `keyboard` library available as fallbacks for setups where SendInput
doesn't register. Nothing here talks to the game process directly.
"""

import ctypes
import time

user32 = ctypes.windll.user32

INPUT_MOUSE = 0
INPUT_KEYBOARD = 1

KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_EXTENDEDKEY = 0x0001

MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

ULONG_PTR = ctypes.c_size_t


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ULONG_PTR),
    ]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ULONG_PTR),
    ]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("union", _INPUTUNION)]


# Minimal US-layout scan code table for the keys this bot cares about
# (digits, letters, function keys, tab, space). Extend as needed.
_SCAN_CODES = {
    "1": 0x02, "2": 0x03, "3": 0x04, "4": 0x05, "5": 0x06,
    "6": 0x07, "7": 0x08, "8": 0x09, "9": 0x0A, "0": 0x0B,
    "q": 0x10, "w": 0x11, "e": 0x12, "r": 0x13, "t": 0x14,
    "y": 0x15, "u": 0x16, "i": 0x17, "o": 0x18, "p": 0x19,
    "a": 0x1E, "s": 0x1F, "d": 0x20, "f": 0x21, "g": 0x22,
    "h": 0x23, "j": 0x24, "k": 0x25, "l": 0x26,
    "z": 0x2C, "x": 0x2D, "c": 0x2E, "v": 0x2F, "b": 0x30,
    "n": 0x31, "m": 0x32,
    "tab": 0x0F, "space": 0x39, "esc": 0x01, "escape": 0x01,
    "f1": 0x3B, "f2": 0x3C, "f3": 0x3D, "f4": 0x3E, "f5": 0x3F,
    "f6": 0x40, "f7": 0x41, "f8": 0x42, "f9": 0x43, "f10": 0x44,
    "f11": 0x57, "f12": 0x58,
}


def scan_code_for(key):
    return _SCAN_CODES.get(key.strip().lower())


def send_scan_code_key(key, hold_seconds=0.03):
    """Most reliable method for games: hardware scan code via SendInput."""
    code = scan_code_for(key)
    if code is None:
        return False

    down = INPUT(type=INPUT_KEYBOARD,
                 union=_INPUTUNION(ki=KEYBDINPUT(0, code, KEYEVENTF_SCANCODE, 0, 0)))
    up = INPUT(type=INPUT_KEYBOARD,
               union=_INPUTUNION(ki=KEYBDINPUT(0, code, KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP, 0, 0)))

    user32.SendInput(1, ctypes.byref(down), ctypes.sizeof(INPUT))
    time.sleep(hold_seconds)
    user32.SendInput(1, ctypes.byref(up), ctypes.sizeof(INPUT))
    return True


def send_pydirectinput_key(key):
    try:
        import pydirectinput
    except ImportError:
        return False
    try:
        pydirectinput.press(key)
        return True
    except Exception:
        return False


def send_keyboard_lib_key(key):
    try:
        import keyboard
    except ImportError:
        return False
    try:
        keyboard.send(key)
        return True
    except Exception:
        return False


def press_key(key, method="auto"):
    """method: 'auto' | 'sendinput' | 'pydirectinput' | 'keyboard'"""
    if method == "sendinput":
        return send_scan_code_key(key)
    if method == "pydirectinput":
        return send_pydirectinput_key(key)
    if method == "keyboard":
        return send_keyboard_lib_key(key)

    # auto: prefer hardware scan code, then fall back
    if send_scan_code_key(key):
        return True
    if send_pydirectinput_key(key):
        return True
    return send_keyboard_lib_key(key)


def _screen_to_absolute(x, y):
    screen_w = user32.GetSystemMetrics(0)
    screen_h = user32.GetSystemMetrics(1)
    return int(x * 65535 / max(screen_w - 1, 1)), int(y * 65535 / max(screen_h - 1, 1))


def click_at(x, y, method="auto"):
    """Move the cursor to (x, y) in screen pixels and left-click."""
    if method == "pydirectinput":
        try:
            import pydirectinput
            pydirectinput.moveTo(int(x), int(y))
            pydirectinput.click()
            return True
        except Exception:
            pass  # fall through to SendInput

    abs_x, abs_y = _screen_to_absolute(int(x), int(y))
    move = INPUT(type=INPUT_MOUSE,
                 union=_INPUTUNION(mi=MOUSEINPUT(abs_x, abs_y, 0,
                                                  MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE, 0, 0)))
    down = INPUT(type=INPUT_MOUSE,
                 union=_INPUTUNION(mi=MOUSEINPUT(abs_x, abs_y, 0,
                                                  MOUSEEVENTF_LEFTDOWN | MOUSEEVENTF_ABSOLUTE, 0, 0)))
    up = INPUT(type=INPUT_MOUSE,
               union=_INPUTUNION(mi=MOUSEINPUT(abs_x, abs_y, 0,
                                                MOUSEEVENTF_LEFTUP | MOUSEEVENTF_ABSOLUTE, 0, 0)))

    user32.SendInput(1, ctypes.byref(move), ctypes.sizeof(INPUT))
    time.sleep(0.02)
    user32.SendInput(1, ctypes.byref(down), ctypes.sizeof(INPUT))
    time.sleep(0.03)
    user32.SendInput(1, ctypes.byref(up), ctypes.sizeof(INPUT))
    return True
