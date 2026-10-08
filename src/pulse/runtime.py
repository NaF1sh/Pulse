"""One Pulse instance per desktop session, with local settings activation."""
import hashlib
import os
from pathlib import Path
import uuid

from PySide6.QtCore import QObject, QLockFile, QFileSystemWatcher, QTimer, Signal


class Session(QObject):
    activated = Signal()

    def __init__(self, parent=None, *, directory=None, identity=None):
        super().__init__(parent)
        from pulse.platforms import runtime_dir, is_windows
        directory = Path(directory) if directory else runtime_dir()
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        identity = identity or '|'.join(os.environ.get(key, '') for key in
                                       ('DISPLAY', 'WAYLAND_DISPLAY', 'DBUS_SESSION_BUS_ADDRESS'))
        if is_windows():
            identity += '|' + os.environ.get('SESSIONNAME', 'console')
        suffix = hashlib.sha256(identity.encode()).hexdigest()[:16]
        self.request = directory / f'pulse-{suffix}.activate'
        # The activation file contains only a nonce, never notification content.
        descriptor = os.open(self.request, os.O_CREAT | os.O_WRONLY, 0o600)
        os.close(descriptor)
        self.seen = self.request.read_text()
        self.lock = QLockFile(str(directory / f'pulse-{suffix}.lock'))
        self.lock.setStaleLockTime(0)
        self.watcher = QFileSystemWatcher(self)
        self.watcher.fileChanged.connect(self.check_activation)
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.check_activation)

    def acquire(self):
        if not self.lock.tryLock(0):
            self.request.write_text(uuid.uuid4().hex)
            return False
        self.watcher.addPath(str(self.request))
        # Polling also covers a coalesced filesystem event or an early second launch.
        self.timer.start()
        QTimer.singleShot(0, self, self.check_activation)
        return True

    def check_activation(self, *_):
        try:
            token = self.request.read_text()[:64]
        except OSError:
            return
        if token and token != self.seen:
            self.seen = token
            self.activated.emit()

    def close(self):
        self.timer.stop()
        paths = self.watcher.files()
        if paths:
            self.watcher.removePaths(paths)
        self.lock.unlock()
