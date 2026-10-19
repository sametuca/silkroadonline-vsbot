"""Look and feel: a light, rounded, Apple-like theme that matches the app icon.

Soft grey window, white rounded cards with a hairline border, dark grey text,
the system font and one accent: iOS blue (the icon's pink is used sparingly).
Applied once, before any widget is created.
"""

import os

import customtkinter as ctk
from PIL import Image

from .paths import resource_path

# -- palette (Apple light mode) --------------------------------------------------
BG = "#f5f5f7"          # window
CARD = "#ffffff"        # panels and cards
BORDER = "#e0e0e6"      # hairline around cards
FIELD = "#ececf0"       # inputs and secondary buttons
FIELD_HOVER = "#dedee4"
INSET = "#f5f5f7"       # log area, summary box
TEXT = "#1d1d1f"
MUTED = "#6e6e73"
ACCENT = "#0a7cff"      # iOS blue
ACCENT_HOVER = "#0063d1"
PINK = "#ef6ca8"        # the icon's pink
SUCCESS = "#34c759"
SUCCESS_SOFT = "#dcf5e3"   # finished step pill
SUCCESS_TEXT = "#1e7a3a"
DANGER = "#ff3b30"
DANGER_HOVER = "#d93025"
ERROR_TEXT = "#d70015"
TRACK = "#d9d9de"       # switch / slider rails

FONT = "Segoe UI"       # closest system match to SF on Windows
RADIUS_CARD, RADIUS_CONTROL, RADIUS_PILL = 20, 12, 26

GRAY = {"fg_color": FIELD, "hover_color": FIELD_HOVER, "text_color": TEXT}
RED = {"fg_color": DANGER, "hover_color": DANGER_HOVER, "text_color": "#ffffff"}
CARD_STYLE = {"border_width": 1, "border_color": BORDER}   # pass to the few frames that are real cards


def _pair(color):
    return [color, color]  # CustomTkinter wants (light, dark): the palette is the same in both


def apply():
    """Override CustomTkinter's default theme in place."""
    th = ctk.ThemeManager.theme
    th["CTkFont"] = {"family": FONT, "size": 13, "weight": "normal"}  # already flattened to this OS at load time
    th["CTk"]["fg_color"] = _pair(BG)
    th["CTkToplevel"]["fg_color"] = _pair(BG)
    th["CTkFrame"].update(corner_radius=RADIUS_CARD, fg_color=_pair(CARD), top_fg_color=_pair(FIELD),
                          border_color=_pair(BORDER))
    th["CTkButton"].update(corner_radius=RADIUS_CONTROL, border_width=0, fg_color=_pair(ACCENT),
                           hover_color=_pair(ACCENT_HOVER), text_color=_pair("#ffffff"))
    th["CTkEntry"].update(corner_radius=RADIUS_CONTROL, border_width=0, fg_color=_pair(FIELD),
                          text_color=_pair(TEXT), placeholder_text_color=_pair(MUTED))
    th["CTkOptionMenu"].update(corner_radius=RADIUS_CONTROL, fg_color=_pair(FIELD), button_color=_pair(FIELD_HOVER),
                               button_hover_color=_pair("#cfcfd6"), text_color=_pair(TEXT),
                               dropdown_fg_color=_pair(CARD), dropdown_hover_color=_pair(FIELD),
                               dropdown_text_color=_pair(TEXT))
    th["CTkSwitch"].update(fg_color=_pair(TRACK), progress_color=_pair(SUCCESS), button_color=_pair("#ffffff"),
                           button_hover_color=_pair("#f4f4f4"), text_color=_pair(TEXT))
    th["CTkSlider"].update(fg_color=_pair(TRACK), progress_color=_pair(ACCENT), button_color=_pair(ACCENT),
                           button_hover_color=_pair(ACCENT_HOVER))
    th["CTkCheckBox"].update(corner_radius=7, fg_color=_pair(ACCENT), hover_color=_pair(ACCENT_HOVER),
                             border_color=_pair("#c7c7cc"), checkmark_color=_pair("#ffffff"), text_color=_pair(TEXT))
    th["CTkTextbox"].update(corner_radius=RADIUS_CONTROL, fg_color=_pair(INSET), text_color=_pair(TEXT),
                            scrollbar_button_color=_pair("#c7c7cc"), scrollbar_button_hover_color=_pair("#aeaeb2"))
    th["CTkLabel"].update(text_color=_pair(TEXT))


def _asset(name):
    path = resource_path("assets", name)
    return path if os.path.isfile(path) else None


def logo(size):
    """The transparent gradient logo (for dark surfaces) as a CTkImage, or None if the asset is missing."""
    path = _asset("logo.png")
    return ctk.CTkImage(Image.open(path), size=(size, size)) if path else None


def app_icon(size):
    """The rounded-square app icon as a CTkImage, or None if the asset is missing."""
    path = _asset("app_icon.png")
    return ctk.CTkImage(Image.open(path), size=(size, size)) if path else None


def set_icon(window):
    """Give a window the app icon. CustomTkinter installs its own icon ~200 ms after creation, so wait for it."""
    path = _asset("icon.ico")
    if not path:
        return

    def apply_icon():
        try:
            window.iconbitmap(path)
        except Exception:
            pass  # a window that is already closed, or no icon support: the default icon is fine
    window.after(300, apply_icon)
