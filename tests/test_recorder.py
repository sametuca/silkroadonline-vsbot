from srbot.detect import Detection
from srbot.recorder import Dataset, Recorder, sprite_box


def det(name="Mangyang", box=(100, 100, 60, 13), source="ocr"):
    x, y, w, h = box
    return Detection(name, name, 1.0, box, (x + w // 2, y + h + 18), source)


def test_sprite_box_sits_below_label_and_is_clamped(scene):
    frame = scene([])
    x, y, w, h = sprite_box(det(), frame.shape)
    assert y >= 100 + 13 - 3 and 12 <= w <= 40 and h > 20
    # label at the very bottom-right: the box must stay inside the frame
    x, y, w, h = sprite_box(det(box=(770, 620, 60, 13)), frame.shape)
    assert x + w <= 802 and y + h <= 632


def test_dataset_writes_yolo_files(tmp_path, scene):
    ds = Dataset(str(tmp_path))
    assert ds.save(scene([]), [det(), det("Cave Bat", (300, 200, 55, 13))]) == 2
    assert ds.classes == ["Mangyang", "Cave Bat"]
    (label_file,) = (tmp_path / "labels").iterdir()
    rows = [r.split() for r in label_file.read_text().splitlines()]
    assert [r[0] for r in rows] == ["0", "1"]
    assert all(0 <= float(v) <= 1 for r in rows for v in r[1:])
    assert ds.count() == 1
    # class ids survive a reload
    assert Dataset(str(tmp_path)).class_id("Cave Bat") == 1


def test_model_detections_are_never_recorded(tmp_path, scene):
    ds = Dataset(str(tmp_path))
    assert ds.save(scene([]), [det(source="model")]) == 0
    rec = Recorder(ds)
    rec.enabled = True
    assert rec.maybe_save(scene([]), [det(source="model")]) is False


def test_recorder_skips_duplicates_and_respects_enabled(tmp_path, scene):
    rec = Recorder(Dataset(str(tmp_path)))
    frame = scene([])
    assert rec.maybe_save(frame, [det()]) is False  # disabled
    rec.enabled = True
    assert rec.maybe_save(frame, [det()]) is True
    rec._last_time = 0  # pretend the throttle interval passed
    assert rec.maybe_save(frame, [det()]) is False  # identical frame
    assert rec.saved == 1
