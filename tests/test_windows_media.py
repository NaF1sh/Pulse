import asyncio
import json
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock

import pytest
from PySide6.QtCore import QCoreApplication

from pulse.sources.windows_media import WindowsMedia
from pulse.sources.windows_media_worker import control, sample_session, snapshot

_APP = QCoreApplication.instance() or QCoreApplication([])


def session(service='player', state='PLAYING', title='A song'):
    caps = NS(is_play_enabled=True, is_pause_enabled=True, is_play_pause_toggle_enabled=False, is_next_enabled=True, is_previous_enabled=False)
    info = NS(playback_status=NS(name=state), controls=caps)
    return NS(source_app_user_model_id=service, get_playback_info=lambda: info,
              try_get_media_properties_async=AsyncMock(return_value=NS(title=title, artist='Artist', thumbnail=None)),
              try_pause_async=AsyncMock(return_value=True), try_play_async=AsyncMock(return_value=True),
              try_skip_next_async=AsyncMock(return_value=True))


def manager(*sessions):
    return NS(get_sessions=lambda: sessions, get_current_session=lambda: sessions[0] if sessions else None)


def test_worker_metadata_and_stopped_player():
    sample = asyncio.run(sample_session(session(title='日本語 🎵')))
    assert sample['title'] == '日本語 🎵'
    assert sample['status'] == 'Playing'
    assert sample['artist'] == 'Artist'
    assert sample['capabilities']['CanGoPrevious'] is False
    assert asyncio.run(sample_session(session(state='STOPPED'))) is None
    assert asyncio.run(sample_session(session(title=''))) is None


def test_worker_one_failed_player_does_not_hide_others():
    broken = session('broken')
    broken.try_get_media_properties_async.side_effect = OSError('Player closed')
    samples = asyncio.run(snapshot(manager(broken, session('working'))))
    assert [s['service'] for s in samples] == ['working']
    with pytest.raises(RuntimeError, match='did not provide'):
        asyncio.run(snapshot(manager(broken)))
    assert asyncio.run(snapshot(manager())) == []


def test_missing_artwork_keeps_track(monkeypatch):
    import pulse.sources.windows_media_worker as worker
    monkeypatch.setattr(worker, 'thumbnail_url', AsyncMock(side_effect=OSError('Cover unavailable')))
    assert asyncio.run(sample_session(session()))['title'] == 'A song'


def test_actions_target_selected_session_and_respect_capabilities():
    paused = session('paused', 'PAUSED')
    playing = session('playing')
    sessions = manager(paused, playing)
    asyncio.run(control(sessions, 'playing', 'toggle'))
    playing.try_pause_async.assert_awaited_once()
    paused.try_play_async.assert_not_awaited()
    asyncio.run(control(sessions, 'paused', 'toggle'))
    paused.try_play_async.assert_awaited_once()
    with pytest.raises(RuntimeError, match='did not accept'):
        asyncio.run(control(sessions, 'playing', 'previous'))
    with pytest.raises(RuntimeError, match='closed'):
        asyncio.run(control(sessions, 'missing', 'next'))
    with pytest.raises(RuntimeError, match='ambiguous'):
        asyncio.run(control(manager(playing, playing), 'playing', 'next'))
    playing.try_skip_next_async.return_value = False
    with pytest.raises(RuntimeError, match='did not accept'):
        asyncio.run(control(sessions, 'playing', 'next'))


def publish(source, *sessions):
    source.received(0, json.dumps({'samples': asyncio.run(snapshot(manager(*sessions)))}), '')


def test_adapter_prefers_playing_keeps_selection_and_clears():
    source = WindowsMedia()
    notifications, clears, statuses = [], [], []
    source.notification.connect(notifications.append)
    source.cleared.connect(lambda: clears.append(True))
    source.status.connect(statuses.append)
    paused, playing = session('paused', 'PAUSED'), session('playing')
    publish(source, paused, playing)
    assert source.selected['service'] == 'playing'
    assert source.controls['toggle'] and not source.controls['previous']
    publish(source, session('new-player'), playing)
    assert source.selected['service'] == 'playing'
    assert len(notifications) == 1
    publish(source, paused)
    assert source.selected['status'] == 'Paused'
    publish(source)
    assert not source.controls['available']
    assert clears == [True]
    assert 'Waiting' in statuses[-1]
    source.received(-1, '', '')
    assert 'retry' in statuses[-1]
    publish(source, playing)
    assert source.controls['available']
    assert 'Connected' in statuses[-1]
    source.stop()
    publish(source, paused)
    assert source.selected['service'] == 'playing'


def test_adapter_dispatch_and_shutdown(monkeypatch):
    source = WindowsMedia()
    calls = []
    monkeypatch.setattr(source, 'launch', lambda cmd, args: calls.append((cmd, args)))
    publish(source, session('Spotify'))
    source.control('previous')
    source.control('invalid')
    assert not calls
    source.control('toggle')
    assert calls[-1] == (source.action, ['--action', 'toggle', '--service', 'Spotify'])
    source.action.busy = True
    source.poll()
    source.control('next')
    assert len(calls) == 1
    source.action.busy = False
    source.control_finished(1, json.dumps({'error': 'Player refused'}), '')
    assert source.controls['error'] == 'Player refused'
    assert calls[-1] == (source.query, [])
    source.stop()
    assert not source.timer.isActive()
    source.poll()
    assert len(calls) == 2


def test_pythonw_uses_console_interpreter_for_json_pipe(monkeypatch, tmp_path):
    monkeypatch.setattr('pulse.sources.windows_media.sys.executable', str(tmp_path / 'pythonw.exe'))
    assert WindowsMedia().executable == str(tmp_path / 'python.exe')


def test_toggle_only_player():
    player = session()
    caps = player.get_playback_info().controls
    caps.is_pause_enabled = False
    caps.is_play_pause_toggle_enabled = True
    player.try_toggle_play_pause_async = AsyncMock(return_value=True)
    assert asyncio.run(sample_session(player))['capabilities']['CanPause']
    asyncio.run(control(manager(player), 'player', 'toggle'))
    player.try_toggle_play_pause_async.assert_awaited_once()
    player.try_pause_async.assert_not_awaited()


@pytest.mark.parametrize('flags, expected', [([], True), (['--no-music'], False), (['--demo'], False)])
def test_windows_launch_enables_music_except_opt_out_and_demo(tmp_path, flags, expected):
    import os
    import subprocess
    import sys
    script = """
import sys
import pulse.main as app
from pulse.sources.windows_media import WindowsMedia
app.is_windows = lambda: True
WindowsMedia.start = lambda self: print('WINDOWS_MUSIC_STARTED', flush=True)
raise SystemExit(app.main(['--backend', 'offscreen', '--no-tasks', '--no-history', '--quit-after', '0.2', *sys.argv[1:]]))
"""
    env = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
               PYTHONPATH=str(Path(__file__).resolve().parents[1] / 'src'),
               XDG_CONFIG_HOME=str(tmp_path / 'config'), XDG_DATA_HOME=str(tmp_path / 'data'),
               XDG_RUNTIME_DIR=str(tmp_path / 'runtime'))
    result = subprocess.run([sys.executable, '-c', script, *flags], env=env, capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    assert ('WINDOWS_MUSIC_STARTED' in result.stdout) is expected


@pytest.mark.parametrize('size, expected', [(4, 'data:image/png;base64,AQIDBA=='), (2 * 1024 * 1024, '')])
def test_thumbnail_bounded_read_and_cleanup(monkeypatch, size, expected):
    import sys
    from unittest.mock import Mock
    from pulse.sources.windows_media_worker import thumbnail_url
    stream = NS(size=size, content_type='image/png', close=Mock())
    def fill(target):
        target[:] = type(target)('B', [1, 2, 3, 4])
    reader = NS(load_async=AsyncMock(return_value=4), read_bytes=fill,
                detach_stream=Mock(), close=Mock())
    factory = Mock(return_value=reader)
    monkeypatch.setitem(sys.modules, 'winrt.windows.storage.streams', NS(DataReader=factory))
    reference = NS(open_read_async=AsyncMock(return_value=stream))
    assert asyncio.run(thumbnail_url(reference)) == expected
    stream.close.assert_called_once()
    if expected:
        reader.close.assert_called_once()
        reader.detach_stream.assert_called_once()
    else:
        factory.assert_not_called()
