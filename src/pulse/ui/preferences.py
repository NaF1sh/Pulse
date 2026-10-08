"""Runtime preferences, stored separately from the user's TOML configuration."""
from dataclasses import replace
import json
import os
import re
from pathlib import Path
import sqlite3
import tempfile

from PySide6.QtCore import QObject, Property, Signal, Slot

from pulse.settings import default_config_path
from pulse.core.history import History
from pulse.ui.backgrounds import MODES, valid_color, readable_colors, random_color, import_image, register_background


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
                    or (key == 'theme' and value in ('default', 'ocean', 'rose'))
                    or (key == 'background_mode' and value in MODES)
                    or (key == 'background_color' and valid_color(value))
                    or (key == 'background_image' and isinstance(value, str) and re.fullmatch(r'[a-f0-9]{64}\.png', value))
                    or (key in ('background_dim', 'background_position') and type(value) in (int, float) and 0 <= value <= 1)}
        except (OSError, ValueError):
            return {}

    def __init__(self, controller, settings, history_path, parent=None, *, path=None,
                 theme=None, reduced_motion=False):
        super().__init__(parent)
        register_background()
        self.path = Path(path or default_config_path().with_name('preferences.json'))
        self.saved = self.read(self.path)
        self.controller = controller
        self.history_path = history_path
        self._theme = theme or settings.theme
        self._motion = reduced_motion
        self._status = ''
        self._entries = []
        self._history_query = ''
        self._sources = {}
        self._welcome_enabled = False
        self._random_color = random_color()
        self._background_error = ''
        self._last_card_id = None
        controller.changed.connect(self.card_arrived)
        controller._music_visible = self.saved.get('music', True)
        controller.volume_visible = self.saved.get('volume', True)
        controller.musicVisibilityChanged.connect(self._music_changed)

    def save(self, key, value):
        self.save_many({key: value})

    def save_many(self, values):
        self.saved.update(values)
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
        query = self._history_query.casefold().strip()
        return [entry for entry in self._entries if not query or
                query in ' '.join(str(entry.get(key, '')) for key in ('app', 'title', 'body')).casefold()]

    @Slot(str)
    def setHistoryQuery(self, query):
        self._history_query = query
        self.historyChanged.emit()

    def access_history(self, clear=False):
        history = None
        try:
            if Path(self.history_path).exists():
                history = History(self.history_path)
                if clear:
                    count = history.clear()
                    self._status = f'Cleared {count} notifications'
                self._entries = history.recent(1000)
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

    @Property(str, notify=changed)
    def backgroundMode(self):
        return self.saved.get('background_mode', 'theme')

    @Property(str, notify=changed)
    def backgroundColor(self):
        return self.saved.get('background_color', '#594a86')

    @Property(str, notify=changed)
    def backgroundError(self):
        return self._background_error

    @Property('QVariantMap', notify=changed)
    def background(self):
        from PySide6.QtCore import QUrl
        mode = self.backgroundMode
        color = self._random_color if mode == 'random' else self.backgroundColor
        image = self.path.parent / 'backgrounds' / self.saved.get('background_image', 'missing')
        available = image.is_file() and image.suffix == '.png'
        return {'mode': mode, 'custom': mode in ('solid', 'random') or mode == 'image' and available,
                'color': color if mode in ('solid', 'random') else '#101014',
                'colors': readable_colors(color) if mode in ('solid', 'random') else
                          dict(background='#101014', title='#ffffff', body='#f0f0f5', muted='#f0f0f5',
                               accent='#e3daff', progress='#ffffff', border='#726d80'),
                'image': QUrl.fromLocalFile(str(image)).toString() if available and mode == 'image' else '',
                'hasImage': available,
                'dim': min(.8, self.saved.get('background_dim', .2)),
                'position': self.saved.get('background_position', .5)}

    @Slot(str)
    def setBackgroundMode(self, mode):
        if mode not in MODES:
            return
        self._background_error = ''
        self.save('background_mode', mode)

    @Slot(str)
    def setBackgroundColor(self, color):
        if not valid_color(color):
            self._background_error = 'Use a six-digit color, such as #594a86.'
            self.changed.emit()
            return
        self._background_error = ''
        self.save_many({'background_mode': 'solid', 'background_color': color.lower()})

    @Slot()
    def shuffleBackground(self):
        self._random_color = random_color(self._random_color)
        self.changed.emit()

    def card_arrived(self):
        item = self.controller.item
        current_id = item.id if item else None
        if current_id != self._last_card_id:
            self._last_card_id = current_id
            if current_id is not None and self.backgroundMode == 'random':
                self.shuffleBackground()

    @Slot(str)
    def importBackground(self, url):
        try:
            filename = import_image(url, self.path.parent / 'backgrounds')
        except (ValueError, OSError) as error:
            self._background_error = str(error)
            self.changed.emit()
            return
        self._background_error = ''
        self.save_many({'background_image': filename, 'background_mode': 'image'})

    @Slot(float)
    def setBackgroundDim(self, value):
        if 0 <= value <= .8:
            self.save('background_dim', value)

    @Slot(float)
    def setBackgroundPosition(self, value):
        if 0 <= value <= 1:
            self.save('background_position', value)


    @Property(bool, constant=True)
    def desktopSources(self):
        from pulse.platforms import is_windows
        return not is_windows()
