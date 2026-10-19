import time

import cv2

from conftest import add_radar
from srbot import detect, radar
from srbot.config import Config
from srbot.detect import Detection
from srbot.overlay import BLUE, GREEN, RED, OverlayState, build_shapes

SHAPE = (632, 802, 3)


def det(name="Mangyang", box=(300, 300, 60, 13), source="ocr"):
    x, y, w, h = box
    return Detection(name, name, 1.0, box, (x + w // 2, y + h + 18), source)


def test_every_monster_gets_a_green_box_around_label_and_sprite():
    (shape,) = [s for s in build_shapes([det()], SHAPE) if s.kind == "rect"]
    assert shape.color == GREEN
    assert shape.x < 300 and shape.y < 300                 # covers the label...
    assert shape.y + shape.h > 300 + 13 + 20               # ...and reaches down over the sprite


def test_the_attacked_monster_is_red_with_a_tag_and_crosshair():
    mine, other = det(), det(box=(100, 200, 60, 13))
    shapes = build_shapes([mine, other], SHAPE, target=mine.click)
    colors = [s.color for s in shapes if s.kind == "rect"]
    assert colors.count(RED) == 1 and colors.count(GREEN) == 1
    assert any(s.kind == "tag" and s.text == "HEDEF" for s in shapes)
    assert any(s.kind == "circle" and s.color == RED for s in shapes)


def test_model_detections_use_their_own_box():
    shapes = build_shapes([det(box=(120, 140, 40, 50), source="model")], SHAPE)
    assert (shapes[0].x, shapes[0].y, shapes[0].w, shapes[0].h) == (120, 140, 40, 50)


def test_walking_destination_is_a_blue_circle():
    (circle,) = build_shapes([], SHAPE, roam_point=(400, 250))
    assert circle.kind == "circle" and circle.color == BLUE


def test_nothing_is_ever_drawn_on_the_radar():
    on_radar = det(box=(745, 90, 40, 13))
    assert build_shapes([on_radar], SHAPE, roam_point=(760, 100)) == []


def test_old_scans_fade_out_unless_flashing():
    state = OverlayState()
    state.update_scan(SHAPE, [det()])
    now = time.time()
    assert state.shapes(now=now + 0.5) and state.shapes(now=now + 5) == []
    state.flash(3.0)
    assert state.shapes(now=now + 2)


# -- the overlay must not disturb the bot's own screen reading -----------------
def _paint(frame, shapes):
    """Draw the shapes onto a frame the way the overlay window does (2 px outlines)."""
    out = frame.copy()
    for s in shapes:
        bgr = tuple(int(s.color[i:i + 2], 16) for i in (5, 3, 1))
        if s.kind == "rect":
            cv2.rectangle(out, (s.x, s.y), (s.x + s.w, s.y + s.h), bgr, 2)
        elif s.kind == "circle":
            cv2.circle(out, (s.x, s.y), s.w, bgr, 2)
        elif s.kind == "tag":
            cv2.putText(out, s.text, (s.x, s.y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, bgr, 1)
    return out


def test_boxes_do_not_change_what_the_bot_reads(scene):
    frame = add_radar(scene([("Mangyang", 300, 300), ("Mangyang", 150, 220), ("Mangyang", 500, 250)]))
    cfg = Config(monsters=["Mangyang"], excludes=[], detector="ocr")
    before = detect.detect(frame, cfg, mode="ocr")
    assert len(before) == 3
    shapes = build_shapes(before, frame.shape, target=before[0].click, roam_point=(400, 250))
    painted = _paint(frame, shapes)
    after = detect.detect(painted, cfg, mode="ocr")
    assert sorted(d.box for d in after) == sorted(d.box for d in before)
    assert sorted(radar.read_dots(painted)) == sorted(radar.read_dots(frame))
