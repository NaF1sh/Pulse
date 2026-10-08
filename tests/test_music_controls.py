import json
from PySide6.QtCore import QCoreApplication
from pulse.sources.mpris import Mpris, parse_player, PLAYER
from test_system_sources import player

_APP = QCoreApplication.instance() or QCoreApplication([])


def sample(status='Playing', **capabilities):
    data = json.loads(player(status=status))
    caps = dict(CanControl=True, CanPause=True, CanPlay=True, CanGoNext=True, CanGoPrevious=False)
    caps.update(capabilities)
    data['data'][0].update({key: {'type': 'b', 'data': value} for key, value in caps.items()})
    return parse_player(json.dumps(data), 'org.mpris.MediaPlayer2.test')


def test_transport_dispatches_only_supported_actions_to_selected_player():
    source = Mpris()
    source.executable = '/usr/bin/busctl'
    calls = []
    source.action.start = lambda program, args: calls.append((program, args)) or True
    source.samples = [sample()]
    source.publish()
    source.control('previous')
    source.control('Stop')
    assert not calls
    source.control('toggle')
    assert calls[-1][1][-3:] == ['/org/mpris/MediaPlayer2', PLAYER, 'Pause']
    assert calls[-1][1][3] == 'org.mpris.MediaPlayer2.test'
    source.samples = [sample('Paused')]
    source.publish()
    source.control('toggle')
    assert calls[-1][1][-1] == 'Play'
    source.action.busy = True
    source.control('next')
    assert len(calls) == 2
    source.action.busy = False
    source.samples = []
    source.publish()
    assert not source.controls['available']
    source.control('next')
    assert len(calls) == 2


def test_no_control_or_missing_capabilities_disables_buttons():
    source = Mpris()
    for parsed in (sample(CanControl=False), parse_player(player(), 'test')):
        source.samples = [parsed]
        source.publish()
        assert not any(source.controls[key] for key in ('toggle', 'previous', 'next'))
    source.stopping = True
    source.control_finished(1, '', 'denied')
    assert 'did not respond' in source.controls['error']
    source.control_finished(0, '', '')
    assert not source.controls['error']
