import numpy as np
import pytest

from conftest import add_panel, add_real_dead_panel, make_scene
from srbot.target import DEAD_FILL, read_panel


def test_no_panel_on_plain_terrain(scene):
    panel = read_panel(scene([]))
    assert panel.present is False and panel.dead is False


@pytest.mark.parametrize("fill", [1.0, 0.7, 0.35, 0.1])
def test_reads_how_full_the_bar_is(fill):
    panel = read_panel(add_panel(make_scene([]), fill))
    assert panel.present and not panel.dead
    assert panel.fill == pytest.approx(fill, abs=0.04)


def test_empty_bar_means_dead():
    panel = read_panel(add_panel(make_scene([]), 0.0))
    assert panel.present and panel.dead and panel.fill <= DEAD_FILL


def test_a_real_capture_of_a_corpse_is_recognised_as_dead():
    panel = read_panel(add_real_dead_panel(make_scene([])))
    assert panel.present is True
    assert panel.dead is True


def test_dark_terrain_is_not_mistaken_for_the_window():
    night = np.full((600, 800, 3), (14, 18, 16), np.uint8)  # very dark but with no bar/strip structure on top
    night[0:90, 330:470] = (40, 40, 44)                       # not black enough for the name strip
    assert read_panel(night).present is False


def test_small_frames_do_not_crash():
    assert read_panel(np.zeros((40, 100, 3), np.uint8)).present is False
