"""Runtime preferences, stored separately from the user's TOML configuration."""
from dataclasses import replace
import json
import os
from pathlib import Path
import sqlite3
import tempfile

from PySide6.QtCore import QObject, Property, Signal, Slot

from pulse.settings import default_config_path
from pulse.core.history import History


class Preferences(QObject):
    changed = Signal()
    appearanceChanged = Signal()
    historyChanged = Signal()
    sourcesChanged = Signal()
    retryRequested = Signal()

    @staticmethod
    def read(path):
        try:
            data = json.loads(Path(path).read_text())
            if not isinstance(data, dict):
                return {}
            return {key: value for key, value in data.items()
                    if (key in ('music', 'volume', 'dnd', 'motion', 'onboarded', 'quiet_plasma') and type(value) is bool)
                    or (key == 'theme' and value in ('default', 'ocean', 'rose'))}
        except (OSError, ValueError):
            return {}

    def __init__(self, controller, settings, history_path, parent=None, *, path=None,
                 theme=None, reduced_motion=False):
        super().__init__(parent)
        self.path = Path(path or default_config_path().with_name('preferences.json'))
        self.saved = self.read(self.path)
        self.controller = controller
        self.history_path = history_path
        self._theme = theme or settings.theme
        self._motion = reduced_motion
        self._status = ''
        self._entries = []
        self._sources = {}
        self._welcome_enabled = False
        controller._music_visible = self.saved.get('music', True)
        controller.volume_visible = self.saved.get('volume', True)
        controller.musicVisibilityChanged.connect(self._music_changed)

    def save(self, key, value):
        self.saved[key] = value
        temporary = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            with tempfile.NamedTemporaryFile('w', dir=self.path.parent, delete=False) as stream:
                temporary = stream.name
                json.dump(self.saved, stream)
            os.replace(temporary, self.path)
            self._status = 'Saved automatically'
        except OSError as error:
            self._status = f'Could not save preferences: {error}'
        finally:
            if temporary and os.path.exists(temporary):
                os.unlink(temporary)
        self.changed.emit()

    def _music_changed(self):
        self.save('music', self.controller.musicVisible)

    @Property(bool, notify=changed)
    def music(self):
        return self.controller.musicVisible

    @Property(bool, notify=changed)
    def volume(self):
        return self.controller.volume_visible

    @Property(bool, notify=changed)
    def dnd(self):
        return self.controller.manager.rules.dnd

    @Property(bool, notify=changed)
    def motion(self):
        return self._motion

    @Property(str, notify=changed)
    def theme(self):
        return self._theme

    @Property(str, notify=changed)
    def status(self):
        if any(source['problem'] for source in self._sources.values()):
            return 'A connection needs attention — open Status for details'
        return self._status

    @Slot(str)
    def toggle(self, key):
        if key == 'music':
            self.controller.toggle_music()
            return
        if key == 'volume':
            self.controller.volume_visible = not self.volume
            if not self.volume:
                self.controller.remove_cards(lambda item: str(item.kind) == 'level')
            value = self.volume
        elif key == 'dnd':
            self.controller.manager.rules = replace(self.controller.manager.rules, dnd=not self.dnd)
            self.controller.remove_cards(lambda item: not self.controller.manager.rules.allows(item))
            if self.controller.media and not self.controller.manager.rules.allows(self.controller.media):
                self.controller.clear_media()
            value = self.dnd
        elif key == 'quiet_plasma':
            value = not self.quiet_plasma
        elif key == 'motion':
            self._motion = not self._motion
            value = self._motion
            self.appearanceChanged.emit()
        else:
            return
        self.save(key, value)

    @Slot(str)
    def selectTheme(self, name):
        if name not in ('default', 'ocean', 'rose'):
            return
        self._theme = name
        self.save('theme', name)
        self.appearanceChanged.emit()

    @Property('QVariantList', notify=historyChanged)
    def entries(self):
        return self._entries

    def access_history(self, clear=False):
        history = None
        try:
            if Path(self.history_path).exists():
                history = History(self.history_path)
                if clear:
                    count = history.clear()
                    self._status = f'Cleared {count} notifications'
                self._entries = history.recent(100)
            else:
                self._entries = []
                self._status = 'No saved notifications'
        except (OSError, sqlite3.Error) as error:
            self._status = f'History unavailable: {error}'
        finally:
            if history is not None:
                history.close()
        self.historyChanged.emit()
        self.changed.emit()

    @Slot()
    def refreshHistory(self):
        self.access_history()

    @Slot()
    def clearHistory(self):
        self.access_history(clear=True)

    @Property(bool, notify=changed)
    def welcomeNeeded(self):
        return self._welcome_enabled and not self.saved.get('onboarded', False)

    def enable_welcome(self):
        self._welcome_enabled = True
        self.changed.emit()

    @Slot()
    def completeWelcome(self):
        self.save('onboarded', True)

    @Slot()
    def previewNotification(self):
        from pulse.core.models import Notification
        self.controller.submit(Notification(-100, 'Pulse', 'A little less interruption',
                                            'Your notifications, close at hand.', timeout=6), record_history=False)
        self._status = 'Preview paused by Do not disturb' if self.dnd else 'Preview shown on your desktop'
        self.changed.emit()

    @Property('QVariantList', notify=sourcesChanged)
    def sources(self):
        return list(self._sources.values())

    def source_status(self, name, detail, *, problem=False):
        self._sources[name] = {'name': name, 'detail': detail, 'problem': problem}
        self.sourcesChanged.emit()
        self.changed.emit()

    @Slot()
    def retryConnections(self):
        self.retryRequested.emit()

    @Property(bool, notify=changed)
    def quiet_plasma(self):
        return self.saved.get('quiet_plasma', False)
