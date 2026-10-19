"""Administrator rights are mandatory: a normal start must elevate itself, never run without them."""

import pytest

import main
from srbot import winutil


@pytest.fixture
def fake_env(monkeypatch):
    calls = {"relaunch": [], "box": []}
    monkeypatch.delenv(main.NO_ADMIN_ENV, raising=False)
    monkeypatch.setattr(main.ctypes.windll.user32, "MessageBoxW",
                        lambda *a: calls["box"].append(a) or 1, raising=False)
    monkeypatch.setattr(main.sys, "argv", ["main.py"])
    return calls, monkeypatch


def test_already_admin_just_continues(fake_env):
    calls, mp = fake_env
    mp.setattr(winutil, "is_admin", lambda: True)
    main.ensure_admin()
    assert calls["box"] == []


def test_not_admin_relaunches_elevated_and_exits(fake_env):
    calls, mp = fake_env
    mp.setattr(winutil, "is_admin", lambda: False)
    mp.setattr(winutil, "relaunch_as_admin", lambda args: calls["relaunch"].append(args) or True)
    with pytest.raises(SystemExit) as stop:
        main.ensure_admin()
    assert stop.value.code == 0 and calls["relaunch"] == [[main.ELEVATED_FLAG]]
    assert calls["box"] == []


def test_declined_uac_explains_and_exits_instead_of_running(fake_env):
    calls, mp = fake_env
    mp.setattr(winutil, "is_admin", lambda: False)
    mp.setattr(winutil, "relaunch_as_admin", lambda args: False)  # the user pressed "No" in the UAC prompt
    with pytest.raises(SystemExit) as stop:
        main.ensure_admin()
    assert stop.value.code == 1
    assert len(calls["box"]) == 1 and "yönetici" in calls["box"][0][1].lower() or "administrator" in calls["box"][0][1].lower()


def test_elevated_copy_that_is_still_not_admin_does_not_loop(fake_env):
    calls, mp = fake_env
    mp.setattr(main.sys, "argv", ["main.py", main.ELEVATED_FLAG])
    mp.setattr(winutil, "is_admin", lambda: False)
    mp.setattr(winutil, "relaunch_as_admin", lambda args: calls["relaunch"].append(args) or True)
    with pytest.raises(SystemExit) as stop:
        main.ensure_admin()
    assert stop.value.code == 1 and calls["relaunch"] == []  # never asks to elevate a second time


def test_developer_escape_hatch(fake_env):
    calls, mp = fake_env
    mp.setenv(main.NO_ADMIN_ENV, "1")
    mp.setattr(winutil, "is_admin", lambda: False)
    main.ensure_admin()
    assert calls["box"] == []
