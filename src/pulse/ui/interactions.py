"""User-triggered app launching and KDE notification action invocation."""
import configparser
import os
from pathlib import Path
import re
import shutil
from xml.etree import ElementTree

from PySide6.QtCore import QObject, Signal

from pulse.sources.command import Command


SERVICE = 'org.freedesktop.Notifications'
OBJECT_PATH = '/org/freedesktop/Notifications'
INTERFACE = 'org.kde.NotificationManager'


def desktop_directories():
    home = Path(os.environ.get('XDG_DATA_HOME') or Path.home() / '.local/share')
    roots = [home, *(Path(value) for value in
                    (os.environ.get('XDG_DATA_DIRS') or '/usr/local/share:/usr/share').split(':') if value)]
    return [root / 'applications' for root in roots]


class DesktopApps:
    """Resolve installed desktop entries, never treat notification text as a command."""
    def __init__(self, directories=None):
        self.directories = directories if directories is not None else desktop_directories()
        self.entries = {}
        self.names = {}
        seen = set()
        for directory in self.directories:
            try:
                paths = sorted(Path(directory).rglob('*.desktop'))
            except OSError:
                continue
            for path in paths:
                desktop_id = str(path.relative_to(directory)).replace(os.sep, '-')
                if desktop_id in seen:
                    continue
                seen.add(desktop_id)
                parser = configparser.ConfigParser(interpolation=None, strict=False)
                try:
                    parser.read_string(path.read_text())
                    entry = parser['Desktop Entry']
                    if entry.get('Type') != 'Application' or entry.get('Hidden', '').lower() == 'true':
                        continue
                    if not entry.get('Exec') and entry.get('DBusActivatable', '').lower() != 'true':
                        continue
                except (OSError, UnicodeError, configparser.Error, KeyError):
                    continue
                self.entries[desktop_id] = path
                for name in {entry.get('Name', ''), desktop_id.removesuffix('.desktop')}:
                    if name:
                        self.names.setdefault(name.casefold(), set()).add(path)

    def resolve(self, desktop_entry, app_name):
        if desktop_entry:
            if not re.fullmatch(r'[A-Za-z0-9_.-]+', desktop_entry) or desktop_entry.startswith('.'):
                return None
            desktop_id = desktop_entry if desktop_entry.endswith('.desktop') else desktop_entry + '.desktop'
            return self.entries.get(desktop_id)
        matches = self.names.get(app_name.casefold(), set())
        return next(iter(matches)) if len(matches) == 1 else None


class Interactions(QObject):
    changed = Signal()
    succeeded = Signal(int)
    failed = Signal(str)

    def __init__(self, decoder, parent=None, *, apps=None):
        super().__init__(parent)
        self.decoder = decoder
        self.apps = apps if apps is not None else DesktopApps()
        self.supported = False
        self.pending = None
        self.probe = Command(self)
        self.command = Command(self)
        self.probe.completed.connect(self.probed)
        self.command.completed.connect(self.completed)

    def start(self):
        busctl = shutil.which('busctl')
        if busctl:
            self.probe.start(busctl, ['--user', '--xml-interface', 'introspect', SERVICE, OBJECT_PATH, INTERFACE])

    def probed(self, code, output, error):
        self.supported = False
        if code == 0:
            try:
                root = ElementTree.fromstring(output)
                self.supported = any(
                    interface.get('name') == INTERFACE and any(
                        method.get('name') == 'InvokeAction' and
                        [(arg.get('type'), arg.get('direction', 'in')) for arg in method.findall('arg')]
                        == [('u', 'in'), ('s', 'in')]
                        for method in interface.findall('method'))
                    for interface in root.iter('interface'))
            except ElementTree.ParseError:
                pass
        self.changed.emit()

    def server_id(self, local_id):
        return next((server_id for server_id, value in self.decoder.server_ids.items()
                     if value == local_id), None)

    def action_available(self, notification):
        return self.supported and self.server_id(notification.id) is not None

    def can_open(self, notification):
        return (self.action_available(notification) and any(key == 'default' for key, _ in notification.actions)
                or self.apps.resolve(notification.desktop_entry, notification.app) is not None)

    def perform(self, notification, action=''):
        if self.pending is not None:
            return
        offered = {key for key, _ in notification.actions}
        if action and (action not in offered or not self.action_available(notification)):
            self.failed.emit('This notification action is no longer available.')
            return
        if not action and 'default' in offered and self.action_available(notification):
            action = 'default'
        if action:
            self.pending = (notification, action)
            busctl = shutil.which('busctl')
            if not busctl or not self.command.start(busctl, [
                '--user', 'call', SERVICE, OBJECT_PATH, INTERFACE, 'InvokeAction',
                'us', str(self.server_id(notification.id)), action,
            ]):
                self.pending = None
                self.failed.emit('Could not start the notification action.')
        else:
            self.launch(notification)
        self.changed.emit()

    def launch(self, notification):
        path = self.apps.resolve(notification.desktop_entry, notification.app)
        gio = shutil.which('gio')
        if path is None or gio is None:
            self.pending = None
            self.failed.emit('No installed application could be opened for this notification.')
            return
        self.pending = (notification, '')
        if not self.command.start(gio, ['launch', str(path)]):
            self.pending = None
            self.failed.emit('Could not start the application launcher.')

    def completed(self, code, output, error):
        pending, self.pending = self.pending, None
        if pending is None:
            return
        notification, action = pending
        if code == 0:
            self.succeeded.emit(notification.id)
        elif action == 'default' and self.apps.resolve(notification.desktop_entry, notification.app):
            self.launch(notification)
        else:
            self.failed.emit('Could not complete the notification action or open the app. Please try Plasma’s notification.')
        self.changed.emit()

    def stop(self):
        self.probe.stop()
        self.command.stop()
        self.pending = None
