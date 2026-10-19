"""Writable data directory: project root from source, the exe's folder when frozen."""

import os
import sys


def app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def data_path(*parts):
    return os.path.join(app_dir(), *parts)


def resource_path(*parts):
    """Read-only bundled files (icons): the PyInstaller bundle when frozen, the project root otherwise."""
    base = getattr(sys, "_MEIPASS", None) or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)
