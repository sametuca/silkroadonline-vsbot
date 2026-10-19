"""The animation toolkit with a fake widget and a fake clock: deterministic, no window needed."""

import pytest

from srbot import anim


class Clock:
    now = 100.0


@pytest.fixture(autouse=True)
def fake_clock(monkeypatch):
    Clock.now = 100.0
    monkeypatch.setattr(anim.time, "perf_counter", lambda: Clock.now)


class FakeWidget:
    """Implements just what Animation and Mover use; `run_frames` plays the Tk event loop."""

    def __init__(self):
        self.jobs, self.placed, self.log = {}, {}, []
        self._next = 0

    def after(self, ms, fn):
        self._next += 1
        self.jobs[self._next] = fn
        return self._next

    def after_cancel(self, job):
        self.jobs.pop(job, None)

    def run_frames(self, seconds, step=0.012):
        end = Clock.now + seconds
        while Clock.now < end and self.jobs:
            Clock.now += step
            for job in list(self.jobs):
                self.jobs.pop(job)()

    # geometry manager used by Mover.slide
    def place(self, **kw):
        self.placed.update(kw)
        self.log.append(("place", dict(kw)))

    def place_configure(self, **kw):
        self.placed.update(kw)

    def place_forget(self):
        self.placed = {}
        self.log.append(("forget",))

    def lift(self):
        pass

    def update_idletasks(self):
        self.log.append(("idle",))


def test_easing_endpoints_and_monotonic():
    for ease in (anim.ease_out_cubic, anim.ease_in_out):
        assert ease(0) == pytest.approx(0) and ease(1) == pytest.approx(1)
        values = [ease(i / 20) for i in range(21)]
        assert values == sorted(values)
    assert anim.ease_out_cubic(0.5) > 0.5          # ease-out: fast start


def test_colour_mixing():
    assert anim.mix("#000000", "#ffffff", 0) == "#000000"
    assert anim.mix("#000000", "#ffffff", 1) == "#ffffff"
    assert anim.mix("#ff0000", "#0000ff", 0.5) == "#800080"


def test_animation_runs_to_exactly_one_and_reports_done_once():
    w, seen, done = FakeWidget(), [], []
    anim.Animation(w, 300, seen.append, lambda: done.append(1))
    w.run_frames(1.0)
    assert seen[-1] == 1.0 and seen == sorted(seen) and len(seen) > 5
    assert done == [1]


def test_finish_jumps_to_the_end_and_stops_the_timer():
    w, seen, done = FakeWidget(), [], []
    a = anim.Animation(w, 300, seen.append, lambda: done.append(1))
    a.finish()
    a.finish()                                     # calling it again is harmless
    assert seen[-1] == 1.0 and done == [1] and not w.jobs


def test_slide_in_ends_in_place_and_removes_the_old_view():
    container, new, old = FakeWidget(), FakeWidget(), FakeWidget()
    mover = anim.Mover()
    mover.slide(container, new, old, direction=1)
    assert new.placed["relx"] == pytest.approx(1.0, abs=0.5)    # starts off to the right
    assert ("idle",) in container.log                            # rendered before the clock started
    container.run_frames(1.0)
    assert new.placed["relx"] == 0 and old.placed == {}          # settled; old view placed no more


def test_sliding_back_enters_from_the_left():
    container, new, old = FakeWidget(), FakeWidget(), FakeWidget()
    anim.Mover().slide(container, new, old, direction=-1)
    assert new.placed["relx"] < 0


def test_a_second_slide_completes_the_first_one_instead_of_fighting_it():
    container = FakeWidget()
    a, b, c = FakeWidget(), FakeWidget(), FakeWidget()
    mover = anim.Mover()
    mover.slide(container, b, a, 1)
    container.run_frames(0.05)                     # mid-slide
    mover.slide(container, c, b, 1)                # the user clicks again at once
    assert b.placed["relx"] == 0 and a.placed == {}   # the first slide was finished first
    container.run_frames(1.0)
    assert c.placed["relx"] == 0 and b.placed == {}


def test_colour_tween_ends_on_the_target_colour():
    w, colours = FakeWidget(), []
    anim.tween_color(w, "fg_color", "#0a7cff", "#ff3b30", 260, apply=colours.append)
    w.run_frames(1.0)
    assert colours[-1] == "#ff3b30" and colours[0] != "#ff3b30" and len(set(colours)) > 3
