"""Windows media sessions, sampled by a bounded nonblocking WinRT helper."""
import json
from pathlib import Path
import sys

from PySide6.QtCore import QObject, QTimer, Signal

from pulse.core.models import Kind, Notification
from pulse.sources.command import Command


class WindowsMedia(QObject):
    controlsChanged = Signal()
    notification = Signal(object)
    cleared = Signal()
    status = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected = None
        self.control_error = ''
        self.last_status = None
        self.stopping = False
        self.query = Command(self)
        self.query.completed.connect(self.received)
        self.action = Command(self)
        self.action.completed.connect(self.control_finished)
        self.timer = QTimer(self)
        self.timer.setInterval(3000)
        self.timer.timeout.connect(self.poll)
        executable = Path(sys.executable)
        self.executable = str(executable.with_name('python.exe') if executable.name.lower() == 'pythonw.exe' else executable)

    def launch(self, command, arguments):
        if command.start(self.executable, ['-m', 'pulse.sources.windows_media_worker', *arguments]):
            command.timeout.start(8000)

    def start(self):
        self.stopping = False
        self.timer.start()
        self.poll()

    def stop(self):
        self.stopping = True
        self.timer.stop()
        self.query.stop()
        self.action.stop()

    def poll(self):
        if not self.stopping and not self.query.busy and not self.action.busy:
            self.launch(self.query, [])

    def report(self, text):
        if text != self.last_status:
            self.last_status = text
            self.status.emit(text)

    @staticmethod
    def response(code, output):
        try:
            data = json.loads(output)
            if not isinstance(data, dict):
                raise ValueError()
        except (ValueError, TypeError):
            return {'error': 'Windows media helper did not respond. Pulse will retry.'}
        if code != 0 and 'error' not in data:
            return {'error': 'Windows media helper failed. Pulse will retry.'}
        return data

    def received(self, code, output, error):
        if self.stopping:
            return
        data = self.response(code, output)
        samples = data.get('samples', [])
        playing = [s for s in samples if s['status'] == 'Playing']
        candidates = playing or samples
        previous = (self.selected or {}).get('service')
        selected = next((s for s in candidates if s['service'] == previous), candidates[0] if candidates else None)
        self.report(data.get('error') or ('Connected to Windows media.' if selected else
                    'Waiting for a player to share Windows media controls.'))
        if selected != self.selected:
            self.selected = selected
            self.control_error = ''
            self.controlsChanged.emit()
            if selected:
                self.notification.emit(Notification(-2000001, 'Music', selected['title'],
                    selected['artist'] or 'Media player', timeout=0, kind=Kind.MEDIA,
                    status=selected['status'], artwork=selected['artwork']))
            else:
                self.cleared.emit()

    @property
    def controls(self):
        sample = self.selected or {}
        caps = sample.get('capabilities', {})
        return dict(available=bool(self.selected), busy=self.action.busy, error=self.control_error,
                    previous=caps.get('CanGoPrevious', False), next=caps.get('CanGoNext', False),
                    toggle=caps.get('CanPause' if sample.get('status') == 'Playing' else 'CanPlay', False))

    def control(self, action):
        if self.stopping or action not in ('previous', 'toggle', 'next') or self.action.busy or not self.controls.get(action):
            return
        self.query.stop()  # Discard a sample from before this explicit control.
        self.control_error = ''
        self.launch(self.action, ['--action', action, '--service', self.selected['service']])
        self.controlsChanged.emit()

    def control_finished(self, code, output, error):
        if self.stopping:
            return
        self.control_error = self.response(code, output).get('error', '')
        self.controlsChanged.emit()
        self.poll()
