"""Look and feel: a dark, rounded, Apple-like theme that matches the app icon.

Neutral dark greys, large corner radii, hairline-free surfaces, the system
font, and one accent taken from the icon's blue (the pink end of the icon's
gradient is used sparingly). Applied once, before any widget is created.
"""

import os

import customtkinter as ctk
from PIL import Image

from .paths import resource_path

# -- palette (iOS dark mode greys + the icon's colours) -----------------------
BG = "#1c1c1e"          # window
CARD = "#2c2c2e"        # panels and cards
FIELD = "#3a3a3c"       # inputs and secondary buttons
FIELD_HOVER = "#48484a"
INSET = "#161618"       # log area
TEXT = "#f5f5f7"
MUTED = "#98989d"
ACCENT = "#2f9de8"      # the icon's blue
ACCENT_HOVER = "#2487cc"
PINK = "#ef6ca8"        # the icon's pink
SUCCESS = "#30d158"
DANGER = "#ff453a"
DANGER_HOVER = "#e0392f"
ERROR_TEXT = "#ff6961"

FONT = "Segoe UI"       # closest system match to SF on Windows
RADIUS_CARD, RADIUS_CONTROL, RADIUS_PILL = 20, 12, 26

GRAY = {"fg_color": FIELD, "hover_color": FIELD_HOVER}
RED = {"fg_color": DANGER, "hover_color": DANGER_HOVER}


def _pair(color):
    return [color, color]  # CustomTkinter wants (light, dark): this theme is dark only


def apply():
    """Override CustomTkinter's default theme in place."""
    th = ctk.ThemeManager.theme
    th["CTkFont"] = {"family": FONT, "size": 13, "weight": "normal"}  # already flattened to this OS at load time
    th["CTk"]["fg_color"] = _pair(BG)
    th["CTkToplevel"]["fg_color"] = _pair(BG)
    th["CTkFrame"].update(corner_radius=RADIUS_CARD, fg_color=_pair(CARD), top_fg_color=_pair(FIELD),
                          border_color=_pair(FIELD))
    th["CTkButton"].update(corner_radius=RADIUS_CONTROL, border_width=0, fg_color=_pair(ACCENT),
                           hover_color=_pair(ACCENT_HOVER), text_color=_pair("#ffffff"))
    th["CTkEntry"].update(corner_radius=RADIUS_CONTROL, border_width=0, fg_color=_pair(FIELD),
                          text_color=_pair(TEXT), placeholder_text_color=_pair(MUTED))
    th["CTkOptionMenu"].update(corner_radius=RADIUS_CONTROL, fg_color=_pair(FIELD), button_color=_pair(FIELD_HOVER),
                               button_hover_color=_pair("#5a5a5e"), text_color=_pair(TEXT))
    th["CTkSwitch"].update(fg_color=_pair(FIELD_HOVER), progress_color=_pair(SUCCESS), button_color=_pair("#ffffff"),
                           button_hover_color=_pair("#f0f0f0"), text_color=_pair(TEXT))
    th["CTkSlider"].update(fg_color=_pair(FIELD_HOVER), progress_color=_pair(ACCENT), button_color=_pair("#ffffff"),
                           button_hover_color=_pair("#f0f0f0"))
    th["CTkCheckBox"].update(corner_radius=7, fg_color=_pair(ACCENT), hover_color=_pair(ACCENT_HOVER),
                             border_color=_pair(FIELD_HOVER), checkmark_color=_pair("#ffffff"), text_color=_pair(TEXT))
    th["CTkTextbox"].update(corner_radius=RADIUS_CONTROL, fg_color=_pair(INSET), text_color=_pair(TEXT),
                            scrollbar_button_color=_pair(FIELD_HOVER), scrollbar_button_hover_color=_pair("#5a5a5e"))
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
