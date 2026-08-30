"""A transparent full-screen overlay for picking a screen rectangle."""

import tkinter as tk


def select_screen_region(root, hint_text=""):
    """Show a click-drag overlay and return (left, top, right, bottom) or None."""
    result = {"rect": None}

    overlay = tk.Toplevel(root)
    overlay.attributes("-fullscreen", True)
    overlay.attributes("-alpha", 0.30)
    overlay.attributes("-topmost", True)
    overlay.configure(bg="black")
    overlay.config(cursor="crosshair")
    overlay.grab_set()
    overlay.focus_force()

    canvas = tk.Canvas(overlay, bg="black", highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    if hint_text:
        canvas.create_text(
            overlay.winfo_screenwidth() // 2, 40,
            text=hint_text, fill="white", font=("Segoe UI", 14, "bold"),
        )

    state = {"start": None, "rect_id": None}

    def on_press(event):
        state["start"] = (event.x_root, event.y_root)
        state["rect_id"] = canvas.create_rectangle(
            event.x_root, event.y_root, event.x_root, event.y_root,
            outline="#00ff88", width=2,
        )

    def on_drag(event):
        if state["start"] is None:
            return
        x0, y0 = state["start"]
        canvas.coords(state["rect_id"], x0, y0, event.x_root, event.y_root)

    def on_release(event):
        if state["start"] is None:
            _close()
            return
        x0, y0 = state["start"]
        x1, y1 = event.x_root, event.y_root
        left, right = sorted((int(x0), int(x1)))
        top, bottom = sorted((int(y0), int(y1)))
        if right - left >= 5 and bottom - top >= 5:
            result["rect"] = (left, top, right, bottom)
        _close()

    def on_escape(_event=None):
        result["rect"] = None
        _close()

    def _close():
        overlay.grab_release()
        overlay.destroy()

    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)
    overlay.bind("<Escape>", on_escape)

    overlay.wait_window()
    return result["rect"]


def pick_screen_point(root, hint_text=""):
    """Show a full-screen overlay and return the (x, y) of a single click, or None."""
    result = {"point": None}

    overlay = tk.Toplevel(root)
    overlay.attributes("-fullscreen", True)
    overlay.attributes("-alpha", 0.30)
    overlay.attributes("-topmost", True)
    overlay.configure(bg="black")
    overlay.config(cursor="crosshair")
    overlay.grab_set()
    overlay.focus_force()

    canvas = tk.Canvas(overlay, bg="black", highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    if hint_text:
        canvas.create_text(
            overlay.winfo_screenwidth() // 2, 40,
            text=hint_text, fill="white", font=("Segoe UI", 14, "bold"),
        )

    def _close():
        overlay.grab_release()
        overlay.destroy()

    def on_click(event):
        result["point"] = (event.x_root, event.y_root)
        _close()

    def on_escape(_event=None):
        result["point"] = None
        _close()

    canvas.bind("<ButtonPress-1>", on_click)
    overlay.bind("<Escape>", on_escape)

    overlay.wait_window()
    return result["point"]
