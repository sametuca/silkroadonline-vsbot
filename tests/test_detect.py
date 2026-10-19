from srbot import detect
from srbot.config import Config


def test_finds_known_monster(scene):
    img = scene([("Mangyang", 300, 300)])
    dets = detect.detect(img, Config(monsters=["Mangyang"], excludes=[]), mode="ocr")
    assert len(dets) == 1
    d = dets[0]
    assert d.name == "Mangyang" and d.source == "ocr"
    x, y, w, h = d.box
    assert 290 < x < 310 and 280 < y < 305
    assert d.click[1] > y + h  # click lands below the label, on the sprite


def test_ignores_unlisted_names(scene):
    img = scene([("Mangyang", 300, 300), ("Cave Bat", 100, 200)])
    dets = detect.detect(img, Config(monsters=["Mangyang"], excludes=[]), mode="ocr")
    assert [d.name for d in dets] == ["Mangyang"]


def test_tolerates_ocr_misread(scene):
    img = scene([("Mangyang", 300, 300)])
    dets = detect.detect(img, Config(monsters=["Mangyan9"], excludes=[], match_threshold=70), mode="ocr")
    assert len(dets) == 1


def test_excluded_area_is_skipped(scene):
    img = scene([("Mangyang", 300, 300)])
    cfg = Config(monsters=["Mangyang"], excludes=[[0.3, 0.4, 0.6, 0.6]])
    assert detect.detect(img, cfg, mode="ocr") == []


def test_learn_mode_returns_every_readable_label(scene):
    img = scene([("Mangyang", 300, 300), ("Cave Bat", 100, 200)])
    texts = {d.text for d in detect.detect(img, Config(excludes=[]), learn=True)}
    assert {"Mangyang", "Cave Bat"} <= texts


def test_learn_mode_hides_own_name(scene):
    img = scene([("Murkrow", 400, 330), ("Mangyang", 300, 300)])
    cfg = Config(excludes=[], player_name="Murkrow")
    texts = {d.text for d in detect.detect(img, cfg, learn=True)}
    assert "Murkrow" not in texts and "Mangyang" in texts


def test_empty_scene_has_no_detections(scene):
    assert detect.detect(scene([]), Config(monsters=["Mangyang"], excludes=[]), mode="ocr") == []


def test_forced_ocr_mode():
    assert detect.active_mode(Config(detector="ocr")) == "ocr"


def test_find_targets_groups_same_name_and_skips_player(scene):
    img = scene([("Mangyang", 300, 300), ("Mangyang", 150, 220), ("Mangyang", 500, 250), ("Murkrow", 400, 330)])
    groups = detect.find_targets([img], Config(excludes=[]), player_name="Murkrow")
    assert [(g.name, g.count) for g in groups] == [("Mangyang", 3)]


def test_find_targets_ignores_non_names(scene):
    img = scene([("[7]Exp 12345", 100, 200), ("Cave Bat", 300, 300)])
    groups = detect.find_targets([img], Config(excludes=[]))
    assert [g.name for g in groups] == ["Cave Bat"]


def test_find_targets_merges_frames_and_orders_by_count(scene):
    a = scene([("Mangyang", 300, 300), ("Cave Bat", 100, 200)])
    b = scene([("Mangyang", 300, 300), ("Mangyang", 150, 220)])
    groups = detect.find_targets([a, b], Config(excludes=[]))
    assert [(g.name, g.count) for g in groups] == [("Mangyang", 2), ("Cave Bat", 1)]
