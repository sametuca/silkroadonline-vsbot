"""Small animation toolkit for the Tk front-end: slide, fade and colour tweens.

Everything runs on the Tk event loop (`widget.after`), time-based, so the
duration stays the same on slow machines (frames are simply dropped) and the
UI never blocks. An animation can be `finish()`ed early, which jumps to its
final state; that is what makes clicking through the wizard quickly safe.
"""

import time

FRAME_MS = 12


def ease_out_cubic(k):
    return 1.0 - (1.0 - k) ** 3


def ease_in_out(k):
    return 4 * k ** 3 if k < 0.5 else 1 - (-2 * k + 2) ** 3 / 2


def lerp(a, b, k):
    return a + (b - a) * k


def _rgb(color):
    color = color.lstrip("#")
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def mix(start, end, k):
    """Blend two '#rrggbb' colours: k=0 gives `start`, k=1 gives `end`."""
    a, b = _rgb(start), _rgb(end)
    return "#%02x%02x%02x" % tuple(round(lerp(a[i], b[i], k)) for i in range(3))


class Animation:
    """Calls `update(progress)` with eased progress 0..1 until the duration has passed, then `done()`."""

    def __init__(self, widget, duration_ms, update, done=None, ease=ease_out_cubic):
        self.widget, self.duration = widget, max(duration_ms, 1) / 1000.0
        self.update, self.done, self.ease = update, done, ease
        self.finished = False
        self._job = None
        self._t0 = time.perf_counter()
        self._tick()

    def _tick(self):
        if self.finished:
            return
        k = min(1.0, (time.perf_counter() - self._t0) / self.duration)
        if k >= 1.0:
            self.finish()
            return
        self.update(self.ease(k))
        try:
            self._job = self.widget.after(FRAME_MS, self._tick)
        except Exception:  # the window was destroyed mid-animation
            self.finished = True

    def finish(self):
        """Jump to the end state now."""
        if self.finished:
            return
        self.finished = True
        if self._job is not None:
            try:
                self.widget.after_cancel(self._job)
            except Exception:
                pass
        try:
            self.update(1.0)
            if self.done:
                self.done()
        except Exception:  # widgets may already be gone
            pass


class Mover:
    """Keeps at most one slide running per container; starting a new one completes the old one first."""

    def __init__(self):
        self.current = None

    def slide(self, container, new, old=None, direction=1, duration_ms=320, parallax=0.28):
        """Push `new` in from the side (direction +1: from the right, -1: from the left) over `old`.

        Both are placed with relative coordinates inside `container`; `old` drifts the other way
        by a fraction (parallax) and is removed when the slide ends.
        """
        if self.current:
            self.current.finish()
        new.place(relx=direction, rely=0, relwidth=1, relheight=1)
        new.lift()
        # Draw the new view off-screen first: its first render can be slow, and the clock below must not
        # start until it is ready, or the slide would skip most of its frames.
        container.update_idletasks()

        def update(p):
            new.place_configure(relx=direction * (1 - p))
            if old is not None:
                old.place_configure(relx=-direction * parallax * p)

        def done():
            new.place(relx=0, rely=0, relwidth=1, relheight=1)
            if old is not None and old is not new:
                old.place_forget()
            self.current = None

        self.current = Animation(container, duration_ms, update, done)
        return self.current


def fade_in(window, duration_ms=240):
    """Fade a top-level window from transparent to opaque."""
    try:
        window.attributes("-alpha", 0.0)
    except Exception:
        return None
    return Animation(window, duration_ms, lambda p: _set_alpha(window, p), lambda: _set_alpha(window, 1.0))


def _set_alpha(window, value):
    try:
        window.attributes("-alpha", value)
    except Exception:
        pass


def tween_color(widget, option, start, end, duration_ms=220, apply=None):
    """Animate a colour option (e.g. 'fg_color') of `widget` from `start` to `end`."""
    setter = apply or (lambda color: widget.configure(**{option: color}))
    return Animation(widget, duration_ms, lambda p: setter(mix(start, end, p)), lambda: setter(end),
                     ease=ease_in_out)
