"""Entry point: python main.py"""

import tkinter as tk

from vsbot.gui import BotGUI


def main():
    root = tk.Tk()
    BotGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
