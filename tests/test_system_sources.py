import json
import os
from pathlib import Path
import sys

import pytest
from PySide6.QtCore import QCoreApplication, QEventLoop, QTimer

from pulse.sources.audio import Audio, parse_volume
from pulse.sources.mpris import Mpris, parse_player


def player(status="Playing", title="Track", artist=None):
    return json.dumps({"type": "a{sv}", "data": [{
        "PlaybackStatus": {"type": "s", "data": status},
        "Metadata": {"type": "a{sv}", "data": {
            "xesam:title": {"type": "s", "data": title},
            "xesam:artist": {"type": "as", "data": artist or ["Artist"]},
            "mpris:trackid": {"type": "o", "data": "/track/1"}}}}]})


def test_volume_baseline_updates_mute_and_amplification():
    app = QCoreApplication.instance() or QCoreApplication([])
    source = Audio()
    cards = []
    source.notification.connect(cards.append)
    source.received(0, "Volume: 0.40\n", "")
    assert not cards
    source.received(0, "Volume: 0.40\n", "")
    assert not cards
    source.received(0, "Volume: 0.65\n", "")
    assert cards[-1].value == 0.65
    source.received(0, "Volume: 0.65 [MUTED]\n", "")
    assert cards[-1].value == 0
    assert cards[-1].value_label == "Muted"
    source.received(0, "Volume: 1.25\n", "")
    assert cards[-1].value == 1
    assert cards[-1].value_label == "125%"


@pytest.mark.parametrize("output", ["", "garbage", "Volume: nan", "Volume: -1", "Volume: 100"])
def test_invalid_volume_output_is_rejected(output):
    with pytest.raises(ValueError):
        parse_volume(output)


def test_mpris_parses_and_sanitizes_metadata():
    sample = parse_player(player(title="<b>Track</b>", artist=["First", "Second"]), "player")
    assert sample["title"] == "Track"
    assert sample["artist"] == "First, Second"
    assert sample["status"] == "Playing"
    assert parse_player(player(status="Stopped"), "player") is None


@pytest.mark.parametrize("artwork, expected", [
    ("https://example.com/cover.jpg", "https://example.com/cover.jpg"),
    ("file:///tmp/cover.png", "file:///tmp/cover.png"),
    ("javascript:alert(1)", ""), ("file://remote/cover.png", ""),
    ("https://user:password@example.com/cover.png", ""),
])
def test_mpris_artwork_urls_are_validated(artwork, expected):
    payload = json.loads(player())
    payload["data"][0]["Metadata"]["data"]["mpris:artUrl"] = {"type": "s", "data": artwork}
    assert parse_player(json.dumps(payload), "player")["artwork"] == expected


def test_mpris_changes_do_not_repeat_and_playing_player_wins():
    app = QCoreApplication.instance() or QCoreApplication([])
    source = Mpris()
    cards = []
    cleared = []
    source.notification.connect(cards.append)
    source.cleared.connect(lambda: cleared.append(True))
    source.samples = [parse_player(player(status="Paused"), "a"), parse_player(player(), "b")]
    source.publish()
    assert source.previous[0] == "b"
    assert len(cards) == 1
    source.publish()
    assert len(cards) == 1
    source.samples = [parse_player(player(status="Paused"), "b")]
    source.publish()
    assert cleared == [True]
    assert len(cards) == 1
    assert cards[-1].timeout == 0
    source.samples = []
    source.publish()
    assert source.previous is None


def test_sources_retry_quietly_and_skip_initial_paused_player():
    app = QCoreApplication.instance() or QCoreApplication([])
    audio = Audio()
    errors = []
    audio.status.connect(errors.append)
    audio.received(1, "", "denied")
    audio.received(1, "", "denied")
    assert len(errors) == 1
    music = Mpris()
    cards = []
    music.notification.connect(cards.append)
    music.samples = [parse_player(player(status="Paused"), "a")]
    music.publish()
    assert not cards


def test_duplicate_browser_player_with_cover_art_is_preferred():
    app = QCoreApplication.instance() or QCoreApplication([])
    source = Mpris()
    plain = parse_player(player(), "chromium")
    rich = dict(plain, service="plasma-browser-integration", artwork="https://example.com/cover.jpg")
    source.samples = [plain]
    source.publish()
    source.samples = [plain, rich]
    source.publish()
    assert source.previous[0] == "plasma-browser-integration"


def test_real_process_pipeline_with_fake_system_tools(monkeypatch, tmp_path):
    app = QCoreApplication.instance() or QCoreApplication([])
    busctl = tmp_path / "busctl"
    busctl.write_text(f'#!{sys.executable}\nimport sys\n'
                      f'print({json.dumps(player())} if sys.argv[-1] != "ListNames" else '
                      f'{json.dumps(json.dumps({"type": "as", "data": [["org.mpris.MediaPlayer2.test"]]}))})\n')
    counter = tmp_path / "count"
    wpctl = tmp_path / "wpctl"
    wpctl.write_text(f'#!{sys.executable}\nfrom pathlib import Path\n'
                    f'p = Path({str(counter)!r})\n'
                    'n = int(p.read_text()) if p.exists() else 0\np.write_text(str(n+1))\n'
                    'print("Volume: 0.40" if n == 0 else "Volume: 0.70")\n')
    for program in (busctl, wpctl):
        program.chmod(0o700)
    monkeypatch.setenv("PATH", str(tmp_path) + os.pathsep + os.environ["PATH"])
    music, audio = Mpris(), Audio()
    cards = []
    music.notification.connect(cards.append)
    audio.notification.connect(cards.append)
    music.start()
    audio.start()
    loop = QEventLoop()
    QTimer.singleShot(1250, loop.quit)
    loop.exec()
    music.stop()
    audio.stop()
    assert {str(item.kind) for item in cards} == {"media", "level"}
    assert any(item.value == 0.7 for item in cards)
    assert all(not command.busy for command in (music.query, music.discovery, audio.command))
