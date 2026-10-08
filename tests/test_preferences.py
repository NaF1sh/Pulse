from PySide6.QtCore import QCoreApplication

_APP = QCoreApplication.instance() or QCoreApplication([])

from pulse.core.history import History
from pulse.core.models import Notification, Kind, Priority
from pulse.settings import Settings
from pulse.ui.controller import Controller
from pulse.ui.preferences import Preferences


def make_preferences(tmp_path, **kwargs):
    controller = Controller()
    controller.timer.stop()
    preferences = Preferences(controller, Settings(), tmp_path / 'history.sqlite3',
                              path=tmp_path / 'preferences.json', **kwargs)
    return controller, preferences


def test_visibility_persists_from_gestures_and_settings(tmp_path):
    controller, preferences = make_preferences(tmp_path)
    controller.toggle_music()
    preferences.toggle('volume')
    restored_controller, restored = make_preferences(tmp_path)
    assert not restored.music
    assert not restored.volume
    restored_controller.submit_system(Notification(1, 'Volume', 'Quiet', kind=Kind.LEVEL))
    assert restored_controller.item is None
    assert preferences.path.stat().st_mode & 0o777 == 0o600


def test_dnd_removes_suppressed_queue_but_preserves_critical(tmp_path):
    controller, preferences = make_preferences(tmp_path)
    controller.submit(Notification(1, 'Discord', 'Hello'))
    controller.submit(Notification(2, 'Discord', 'Another'))
    controller.submit(Notification(3, 'Battery', 'Critical', priority=Priority.HIGH))
    preferences.toggle('dnd')
    assert controller.item.id == 3
    assert controller.manager.pending == []
    controller.dismiss()
    assert not controller.active
    assert Preferences.read(preferences.path)['dnd']


def test_history_view_and_clear(tmp_path):
    controller, preferences = make_preferences(tmp_path)
    history = History(preferences.history_path)
    try:
        history.record(Notification(1, 'Discord', 'Hey', body='A message'))
        preferences.refreshHistory()
        assert preferences.entries[0]['body'] == 'A message'
        preferences.clearHistory()
        assert preferences.entries == []
        assert history.recent() == []
    finally:
        history.close()


def test_invalid_preferences_and_unsaved_overrides(tmp_path):
    path = tmp_path / 'preferences.json'
    path.write_text('{"music": "false", "theme": [], "dnd": true}')
    assert Preferences.read(path) == {'dnd': True}
    controller, preferences = make_preferences(tmp_path, theme='ocean', reduced_motion=True)
    preferences.toggle('volume')
    saved = Preferences.read(path)
    assert 'theme' not in saved and 'motion' not in saved
    preferences.selectTheme('rose')
    assert Preferences.read(path)['theme'] == 'rose'


def test_welcome_completion_persists_and_preview_is_not_history(tmp_path):
    controller, preferences = make_preferences(tmp_path)
    history = History(preferences.history_path)
    controller.history = history
    preferences.enable_welcome()
    assert preferences.welcomeNeeded
    preferences.previewNotification()
    assert controller.item.app == 'Pulse'
    assert history.recent() == []
    preferences.completeWelcome()
    assert not preferences.welcomeNeeded
    _, restored = make_preferences(tmp_path)
    restored.enable_welcome()
    assert not restored.welcomeNeeded
    history.close()


def test_source_status_replaces_old_failure(tmp_path):
    _, preferences = make_preferences(tmp_path)
    preferences.source_status('Notifications', 'Disconnected', problem=True)
    preferences.source_status('Notifications', 'Ready')
    assert preferences.sources == [{'name': 'Notifications', 'detail': 'Ready', 'problem': False}]


def test_quiet_plasma_is_opt_in_and_persists(tmp_path):
    _, preferences = make_preferences(tmp_path)
    assert not preferences.quiet_plasma
    preferences.toggle('quiet_plasma')
    assert preferences.quiet_plasma
    _, restored = make_preferences(tmp_path)
    assert restored.quiet_plasma
