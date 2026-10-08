import pytest

from pulse.settings import Settings, default_config_path, load_settings
from pulse.sources.dbus_observer import NotificationDecoder
from test_observer import call


def test_missing_default_config_uses_defaults_but_explicit_path_fails(tmp_path):
    missing = tmp_path / "missing.toml"
    assert load_settings(missing) == Settings()
    with pytest.raises(ValueError, match="does not exist"):
        load_settings(missing, required=True)


def test_valid_settings_and_default_timeout_semantics(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text('[notifications]\ndnd = true\nallow_critical = false\nmuted_apps = [" Music "]\ndefault_timeout = 8\n[appearance]\nreduced_motion = true\n')
    settings = load_settings(path)
    assert settings.rules.dnd
    assert not settings.rules.allow_critical
    assert settings.rules.muted_apps == ("Music",)
    assert settings.reduced_motion
    decoder = NotificationDecoder(settings.default_timeout)
    assert decoder.decode(call(timeout=-1)).timeout == 8
    assert decoder.decode(call(timeout=2000)).timeout == 2
    assert decoder.decode(call(timeout=0)).timeout == 0
    assert decoder.decode(call(urgency=2, timeout=-1)).timeout == 0


@pytest.mark.parametrize("content", [
    "[notifications", '[notifications]\ndnd = "yes"',
    '[notifications]\nmuted_apps = "Music"', '[notifications]\nmuted_apps = [""]',
    "[notifications]\ndefault_timeout = 0", "[notifications]\ndefault_timeout = nan",
    "[notifications]\ndefault_timeout = true", "[notifications]\ndefault_timeout = 3601",
    "[notifications]\ntypo = true", "[unknown]\ndnd = true",
    "notifications = false", '[appearance]\nreduced_motion = "yes"',
])
def test_invalid_settings_are_rejected(tmp_path, content):
    path = tmp_path / "config.toml"
    path.write_text(content)
    with pytest.raises(ValueError):
        load_settings(path)


def test_config_path_respects_xdg(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert default_config_path() == tmp_path / "pulse" / "config.toml"
