"""Silkroad Vision Bot - a screen-vision based auto-hunt tool.

This package intentionally never reads process memory and never touches the
game's network traffic. Everything it does is external automation: it looks
at pixels on screen (like a person would) and sends synthetic keyboard/mouse
input (like a person would). That keeps it clear of anti-cheat systems that
watch the game process or the wire protocol.
"""

__version__ = "2.0.0"
