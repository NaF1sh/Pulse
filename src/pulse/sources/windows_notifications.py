"""Windows toast notifications, sampled by a bounded nonblocking WinRT helper."""
import json
from pathlib import Path
import sys

from PySide6.QtCore import QObject, QTimer, Signal

from pulse.core.models import Notification
from pulse.sources.command import Command


class WindowsNotifications(QObject):
    notification = Signal(object)
    status = Signal(str)
    changed = Signal()
    succeeded = Signal(int)
    failed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.seen = set()
        self.aumids = {}
        self.last_status = None
        self.stopping = False
        self.pending = None
        self.query = Command(self)
        self.query.completed.connect(self.received)
        self.launcher = Command(self)
        self.launcher.completed.connect(self.launched)
        self.remover = Command(self)
        self.timer = QTimer(self)
        self.timer.setInterval(2000)
        self.timer.timeout.connect(self.poll)
        executable = Path(sys.executable)
        self.executable = str(executable.with_name('python.exe') if executable.name.lower() == 'pythonw.exe' else executable)

    def start(self):
        self.stopping = False
        self.timer.start()
        self.poll()

    def stop(self):
        self.stopping = True
        self.timer.stop()
        self.query.stop()
        self.launcher.stop()
        self.remover.stop()

    def can_open(self, notification):
        return bool(self.aumids.get(notification.id))

    def action_available(self, notification):
        return False

    def perform(self, notification, action=''):
        if self.pending is not None:
            return
        aumid = self.aumids.get(notification.id)
        if not aumid:
            self.failed.emit('No application is associated with this notification.')
            return
        self.pending = notification.id
        if not self.launcher.start('explorer.exe', [f'shell:AppsFolder\\{aumid}']):
            self.pending = None
            self.failed.emit('Could not open the application.')
        self.changed.emit()

    def launched(self, code, output, error):
        notification_id, self.pending = self.pending, None
        if notification_id is None:
            return
        self.succeeded.emit(notification_id)
        if self.remover.start(self.executable,
                              ['-m', 'pulse.sources.windows_notifications_worker', '--remove', str(notification_id)]):
            self.remover.timeout.start(8000)
        self.changed.emit()

    def poll(self):
        if not self.stopping and not self.query.busy:
            if self.query.start(self.executable, ['-m', 'pulse.sources.windows_notifications_worker']):
                self.query.timeout.start(8000)

    def report(self, text):
        if text != self.last_status:
            self.last_status = text
            self.status.emit(text)

    def received(self, code, output, error):
        if self.stopping:
            return
        try:
            data = json.loads(output)
            if not isinstance(data, dict):
                raise ValueError()
        except (ValueError, TypeError):
            data = {'error': 'Windows notification helper did not respond. Pulse will retry.'}
        if code != 0 and 'error' not in data:
            data = {'error': 'Windows notification helper failed. Pulse will retry.'}
        if 'error' in data:
            self.report(data['error'])
            return
        self.report('Connected to Windows notifications.')
        samples = data.get('samples', [])
        current_ids = {sample['id'] for sample in samples}
        self.aumids = {sample['id']: sample.get('aumid', '') for sample in samples if sample.get('aumid')}
        for sample in samples:
            if sample['id'] not in self.seen:
                self.notification.emit(Notification(sample['id'], sample['app'], sample['title'], sample['body'],
                                                     timeout=0, desktop_entry=sample.get('aumid', '')))
        self.seen = current_ids
