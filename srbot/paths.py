"""Writable data directory: project root from source, the exe's folder when frozen."""

import os
import sys


def app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def data_path(*parts):
    return os.path.join(app_dir(), *parts)
