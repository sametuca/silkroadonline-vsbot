"""Entry point: python main.py"""

import sys


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "--selftest":
        from srbot.selftest import run
        sys.exit(run(sys.argv[2]))

    from srbot import winutil
    from srbot.gui import App

    winutil.try_set_process_dpi_aware()
    App().mainloop()


if __name__ == "__main__":
    main()
