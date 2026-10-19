import numpy as np

from srbot.yolo import YoloDetector


class FakeSession:
    """Returns one confident box in letterboxed 640x640 space, YOLOv8 layout (1, 4+nc, N)."""

    def __init__(self, cx, cy, w, h, cls, n_classes=2):
        out = np.zeros((1, 4 + n_classes, 8400), np.float32)
        out[0, :4, 0] = (cx, cy, w, h)
        out[0, 4 + cls, 0] = 0.9
        self.out = out

    def run(self, *_):
        return [self.out]


def detector(session):
    d = YoloDetector.__new__(YoloDetector)
    d.classes, d.imgsz, d.session, d.input_name = ["Mangyang", "Cave Bat"], 640, session, "images"
    return d


def test_letterbox_maps_boxes_back_to_frame_pixels():
    # 800x600 frame -> scale 0.8, 80px vertical padding. Box centre (320, 320) in model space
    # is frame point (400, 300); 80x80 model px is 100x100 frame px.
    d = detector(FakeSession(320, 320, 80, 80, cls=1))
    frame = np.zeros((600, 800, 3), np.uint8)
    ((name, conf, box),) = d.predict(frame)
    assert name == "Cave Bat" and conf > 0.85
    assert box == (350, 250, 100, 100)


def test_low_confidence_is_filtered():
    d = detector(FakeSession(320, 320, 80, 80, cls=0))
    assert d.predict(np.zeros((600, 800, 3), np.uint8), conf=0.95) == []
