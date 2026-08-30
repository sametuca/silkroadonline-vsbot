"""Where the app's writable files (profiles, language.json, monsters/) live.

When running from source, that's the project root (one level above this
file). When frozen into a single .exe by PyInstaller, `__file__` resolves
inside the temporary extraction folder (`sys._MEIPASS`) which is wiped
after the process exits - so settings would silently fail to persist. The
app's actual data directory in that case is wherever the .exe itself sits.
"""

import os
import sys


def app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def data_path(*parts):
    return os.path.join(app_dir(), *parts)
