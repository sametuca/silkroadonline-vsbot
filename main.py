"""Entry point: python main.py

The program must run as administrator: games are usually elevated, and Windows
silently drops keys and clicks sent from a non-elevated program to an elevated
one. So a normal start re-launches itself elevated (UAC prompt) and exits.
"""

import ctypes
import os
import sys

ELEVATED_FLAG = "--elevated"   # marks the re-launched copy so a refused elevation cannot loop
NO_ADMIN_ENV = "SRBOT_NO_ADMIN"  # developer escape hatch: run without elevation (input to elevated games is blocked)


def ensure_admin():
    """Return only when running as administrator; otherwise elevate or explain and exit."""
    from srbot import winutil
    from srbot.i18n import t

    if winutil.is_admin() or os.environ.get(NO_ADMIN_ENV) == "1":
        return
    if ELEVATED_FLAG not in sys.argv and winutil.relaunch_as_admin([ELEVATED_FLAG]):
        sys.exit(0)  # the elevated copy takes over
    ctypes.windll.user32.MessageBoxW(0, t("admin_required_text"), t("admin_required_title"), 0x10)
    sys.exit(1)


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "--selftest":
        from srbot.selftest import run
        sys.exit(run(sys.argv[2]))

    ensure_admin()
    sys.argv = [a for a in sys.argv if a != ELEVATED_FLAG]

    from srbot import winutil
    from srbot.gui import App

    winutil.try_set_process_dpi_aware()
    App().mainloop()


if __name__ == "__main__":
    main()
