import json

from srbot.config import Config


def test_roundtrip(tmp_path):
    path = tmp_path / "config.json"
    cfg = Config(monsters=["Mangyang"], attack_keys=["1", "2"])
    cfg.save(path)
    loaded = Config.load(path)
    assert loaded.monsters == ["Mangyang"]
    assert loaded.attack_keys == ["1", "2"]


def test_missing_file_gives_defaults(tmp_path):
    cfg = Config.load(tmp_path / "nope.json")
    assert cfg.monsters == [] and cfg.detector == "auto"
    assert cfg.attack_keys == ["1", "2", "3", "4"]


def test_unknown_and_corrupt_input(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"monsters": ["A"], "removed_option": 1}), encoding="utf-8")
    assert Config.load(path).monsters == ["A"]
    path.write_text(json.dumps({"loot_key": "z"}), encoding="utf-8")  # a removed option from an older config
    assert Config.load(path).monsters == []
    path.write_text("{not json", encoding="utf-8")
    assert Config.load(path).monsters == []


def test_character_name_from_window_title():
    from srbot.winutil import character_name_from_title
    assert character_name_from_title(" [Murkrow] Destiny Online") == "Murkrow"
    assert character_name_from_title("Silkroad Online") == ""


def test_parse_monster_names_from_the_wizard_input():
    from srbot.gui import parse_names
    assert parse_names(" mangyang ,  Mangyang, Cave   Bat ,, ") == ["mangyang", "Cave Bat"]
    assert parse_names("") == [] and parse_names(" , ") == []
