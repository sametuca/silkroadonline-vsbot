import re
from pathlib import Path

import pytest

from srbot import i18n
from srbot.i18n import S, t

PLACEHOLDER = re.compile(r"\{(\w+)\}")
SRC = Path(__file__).resolve().parent.parent / "srbot"


@pytest.fixture(autouse=True)
def restore_language():
    yield
    i18n.set_language("tr")


def test_every_text_exists_in_both_languages():
    for key, (tr, en) in S.items():
        assert tr.strip() and en.strip(), key


def test_placeholders_match_between_languages():
    for key, (tr, en) in S.items():
        assert set(PLACEHOLDER.findall(tr)) == set(PLACEHOLDER.findall(en)), key


def test_every_key_used_in_code_is_defined():
    used = set()
    for path in SRC.glob("*.py"):
        if path.name == "i18n.py":
            continue
        # only literal keys: t("state_" + name) is built dynamically and checked separately
        used |= set(re.findall(r"\bt\(\s*\"(\w+)\"\s*[,)]", path.read_text(encoding="utf-8")))
    assert used, "expected translated strings in the code"
    assert used <= set(S), sorted(used - set(S))


def test_state_names_are_translated():
    from srbot.engine import State
    for state in State:
        assert f"state_{state.name.lower()}" in S


def test_switching_language_changes_the_text():
    i18n.set_language("en")
    assert t("start") == "START" and t("bot_killed", name="Wolf", n=3) == "Wolf died (total 3)."
    i18n.set_language("tr")
    assert t("start") == "BAŞLAT"
    i18n.set_language("xx")  # unknown codes fall back to Turkish
    assert i18n.get_language() == "tr"


def test_placeholder_named_key_does_not_clash():
    i18n.set_language("en")
    assert t("bot_key_sent", key="2") == "Attack key sent: 2"
