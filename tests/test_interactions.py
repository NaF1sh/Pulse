from pathlib import Path

from PySide6.QtCore import QCoreApplication
import pytest

from pulse.core.models import Notification
from pulse.sources.dbus_observer import NotificationDecoder
from pulse.ui.controller import Controller
from pulse.ui.interactions import DesktopApps, Interactions, INTERFACE


APP = QCoreApplication.instance() or QCoreApplication([])
XML = f'''<node><interface name="{INTERFACE}"><method name="InvokeAction">
<arg type="u" direction="in"/><arg type="s" direction="in"/>
</method></interface></node>'''


def desktop(directory, filename='discord.desktop', name='Discord', extra=''):
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / filename
    path.write_text(f'[Desktop Entry]\nType=Application\nName={name}\nExec=discord %U\n{extra}')
    return path


def backend(tmp_path, monkeypatch):
    monkeypatch.setattr('pulse.ui.interactions.shutil.which', lambda name: '/usr/bin/' + name)
    decoder = NotificationDecoder()
    path = desktop(tmp_path)
    interactions = Interactions(decoder, apps=DesktopApps([tmp_path]))
    commands = []
    monkeypatch.setattr(interactions.command, 'start', lambda program, args: commands.append((program, args)) or True)
    return interactions, commands, path


def test_desktop_ids_and_unique_name_fallback_respect_overrides(tmp_path):
    system = tmp_path / 'system'
    user = tmp_path / 'user'
    system_path = desktop(system)
    apps = DesktopApps([user, system])
    assert apps.resolve('discord', '') == system_path
    assert apps.resolve('discord.desktop', '') == system_path
    assert apps.resolve('', 'DISCORD') == system_path
    desktop(user, extra='Hidden=true\n')
    apps = DesktopApps([user, system])
    assert apps.resolve('discord', '') is None
    assert apps.resolve('', 'Discord') is None
    desktop(user, filename='other.desktop')
    desktop(system, filename='third.desktop')
    assert DesktopApps([user, system]).resolve('', 'Discord') is None


@pytest.mark.parametrize('value', ['/tmp/evil.desktop', '../discord', 'discord;echo test', '$(echo test)', 'a/b'])
def test_desktop_hint_cannot_supply_command_or_arbitrary_file(tmp_path, value):
    desktop(tmp_path)
    assert DesktopApps([tmp_path]).resolve(value, 'Discord') is None


def test_click_uses_default_action_with_real_server_id(tmp_path, monkeypatch):
    interactions, commands, _ = backend(tmp_path, monkeypatch)
    item = Notification(1, 'Discord', 'Hello', actions=(('default', 'Open'), ('mark', 'Mark read')))
    interactions.decoder.server_ids[42] = 1
    interactions.probed(0, XML, '')
    assert interactions.action_available(item)
    assert interactions.can_open(item)
    successes = []
    interactions.succeeded.connect(successes.append)
    interactions.perform(item)
    assert commands[0][1][-4:] == ['InvokeAction', 'us', '42', 'default']
    assert successes == []
    interactions.completed(0, '', '')
    assert successes == [1]


def test_open_falls_back_to_installed_desktop_and_uses_argument_list(tmp_path, monkeypatch):
    interactions, commands, path = backend(tmp_path, monkeypatch)
    item = Notification(1, 'Discord', 'Hello', desktop_entry='discord')
    interactions.perform(item)
    assert commands == [('/usr/bin/gio', ['launch', str(path)])]


def test_failed_default_falls_back_but_nondefault_actions_never_launch_app(tmp_path, monkeypatch):
    interactions, commands, path = backend(tmp_path, monkeypatch)
    interactions.decoder.server_ids[42] = 1
    interactions.probed(0, XML, '')
    item = Notification(1, 'Discord', 'Hello', actions=(('default', 'Open'), ('mark', 'Mark read')))
    interactions.perform(item)
    interactions.completed(1, '', 'unsupported')
    assert commands[-1] == ('/usr/bin/gio', ['launch', str(path)])
    interactions.completed(0, '', '')
    interactions.perform(item, 'mark')
    count = len(commands)
    interactions.completed(1, '', 'failed')
    assert len(commands) == count


def test_invalid_expired_and_busy_actions_do_not_execute(tmp_path, monkeypatch):
    interactions, commands, _ = backend(tmp_path, monkeypatch)
    item = Notification(1, 'Discord', 'Hello', actions=(('mark', 'Mark read'),))
    interactions.perform(item, 'mark')
    assert commands == []
    interactions.probed(0, XML, '')
    interactions.decoder.server_ids[42] = 1
    interactions.perform(item, 'delete')
    assert commands == []
    interactions.perform(item, 'mark')
    interactions.perform(item, 'mark')
    assert len(commands) == 1
    interactions.completed(0, '', '')
    interactions.decoder.server_ids.clear()
    interactions.perform(item, 'mark')
    assert len(commands) == 1


def test_capability_probe_rejects_missing_or_wrong_signature(tmp_path, monkeypatch):
    interactions, _, _ = backend(tmp_path, monkeypatch)
    for code, xml in [(1, XML), (0, '<node/>'), (0, 'invalid'), (0, XML.replace('type="u"', 'type="s"'))]:
        interactions.probed(code, xml, '')
        assert not interactions.supported


def test_controller_keeps_card_on_failure_and_closes_only_successful_id(tmp_path, monkeypatch):
    interactions, commands, _ = backend(tmp_path, monkeypatch)
    controller = Controller()
    controller.timer.stop()
    controller.set_interactions(interactions)
    controller.submit(Notification(1, 'Unknown', 'Keep me'))
    controller.activate(1)
    assert controller.active and controller.actionError
    controller.activate(999)
    assert commands == []
    controller.submit(Notification(1, 'Discord', 'Hello'))
    controller.activate(1)
    controller.submit(Notification(2, 'Discord', 'Queued'))
    interactions.completed(0, '', '')
    assert controller.item.id == 2
