"""Task status for the floating island; all external actions require a click."""
from datetime import datetime
from pathlib import Path
import sqlite3
import time

from PySide6.QtCore import QObject, Property, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices
from pulse.core.models import Kind, Notification
from pulse.tasks.store import TaskStore, validate_target

ATTENTION = ('needs-permission', 'needs-input', 'failed')
LABELS = {'working': 'Working', 'needs-input': 'Needs your answer', 'needs-permission': 'Needs permission',
          'done': 'Finished', 'failed': 'Failed', 'cancelled': 'Cancelled'}


class Tasks(QObject):
    changed = Signal()

    def __init__(self, parent=None, *, clock=time.time, opener=QDesktopServices.openUrl):
        super().__init__(parent)
        self.clock = clock
        self.opener = opener
        self.store = None
        self.rows = []
        self._error = ''
        self._read_failed = False
        self._toast = None
        self._toast_until = 0
        self._known = {}
        self.timer = QTimer(self)
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.poll)

    def start(self, path=None):
        try:
            self.store = TaskStore(path)
            self.poll()
            self.timer.start()
        except (OSError, sqlite3.Error) as error:
            self._error = f'Task connection unavailable: {error}'
            self.changed.emit()

    def stop(self):
        self.timer.stop()
        if self.store is not None:
            self.store.close()
            self.store = None

    def poll(self):
        if self.store is None:
            return
        try:
            rows = self.store.list()
        except sqlite3.Error:
            if not self._read_failed:
                self._read_failed = True
                self._error = 'Task updates are temporarily unavailable. Retrying…'
                self.changed.emit()
            return
        now = self.clock()
        changed = rows != self.rows or self._read_failed
        if self._read_failed:
            self._read_failed = False
            self._error = ''
        for row in reversed(rows):
            if self._known.get(row['id']) != row['revision'] and row['state'] == 'done' and not row['dismissed'] and now - row['updated'] < 10:
                self._toast = row['id']
                self._toast_until = now + 6
        self._known = {row['id']: row['revision'] for row in rows}
        self.rows = rows
        if self._toast and now >= self._toast_until:
            self._toast = None
            changed = True
        if changed:
            self.changed.emit()

    @Property('QVariantList', notify=changed)
    def entries(self):
        return [dict(row, label=LABELS[row['state']], updatedLabel=datetime.fromtimestamp(row['updated']).strftime('%H:%M'),
                     hasTarget=bool(row['target'])) for row in sorted(self.rows, key=lambda row:
                     (0 if row['state'] in ATTENTION and not row['dismissed'] else 1 if row['state'] == 'working' and not row['dismissed'] else 2, -row['updated']))]

    @Property('QVariantMap', notify=changed)
    def summary(self):
        active = self.rows
        return dict(total=len(self.rows), working=sum(row['state'] == 'working' for row in active),
                    attention=sum(row['state'] in ATTENTION for row in active),
                    error=self._error, connected=self.store is not None)

    @property
    def head(self):
        active = [row for row in self.rows if not row['dismissed']]
        return next((row for row in active if row['state'] in ATTENTION), None) or next(
            (row for row in active if row['id'] == self._toast), None) or next(
            (row for row in active if row['state'] == 'working'), None)

    @property
    def card(self):
        row = self.head
        if row is None:
            return None
        working = self.summary['working']
        title = f'{working} tasks working' if row['state'] == 'working' and working > 1 else row['title']
        label = LABELS[row['state']]
        body = label + ' · ' + (row['message'] or row['source'])
        progress = row['progress'] if row['state'] == 'working' else None
        return Notification(-4000001, 'Pulse Tasks', title, body, timeout=0,
                            kind=Kind.PROGRESS if progress is not None else Kind.MESSAGE,
                            value=progress or 0, value_label=f'{round(progress * 100)}%' if progress is not None else '', status='Task')

    @Slot(str)
    def dismiss(self, task_id):
        if self.store:
            try:
                self.store.dismiss(task_id)
                self.poll()
            except sqlite3.Error:
                self._error = 'Could not dismiss this alert. Try again.'
                self.changed.emit()

    @Slot(str)
    def remove(self, task_id):
        if self.store:
            try:
                self.store.remove(task_id)
                self.poll()
            except sqlite3.Error:
                self._error = 'Could not remove this task. Try again.'
                self.changed.emit()

    @Slot()
    def clearFinished(self):
        if self.store:
            try:
                self.store.clear_finished()
                self.poll()
            except sqlite3.Error:
                self._error = 'Could not clear finished tasks. Try again.'
                self.changed.emit()

    @Slot(str)
    def open(self, task_id):
        row = next((row for row in self.rows if row['id'] == task_id), None)
        if not row or not row['target']:
            return
        try:
            url = QUrl(validate_target(row['target']))
            if url.isLocalFile():
                path = Path(url.toLocalFile()).resolve()
                allowed = {'.txt', '.log', '.md', '.json', '.pdf', '.png', '.jpg', '.jpeg', '.webp', '.diff', '.patch', '.csv'}
                if not path.exists() or not (path.is_dir() or path.suffix.lower() in allowed):
                    raise ValueError('Open a results folder, text log, document, or HTTPS link. Executable files cannot be opened here.')
                url = QUrl.fromLocalFile(str(path))
            if not self.opener(url):
                raise ValueError('Could not open this task’s result. Return to the original tool.')
            self._error = ''
        except (ValueError, OSError) as error:
            self._error = str(error)
        self.changed.emit()
