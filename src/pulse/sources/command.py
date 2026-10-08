"""Nonblocking, bounded command runner for read-only system sources."""
from PySide6.QtCore import QObject, QProcess, QProcessEnvironment, QTimer, Signal


class Command(QObject):
    completed = Signal(int, str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.process = QProcess(self)
        environment = QProcessEnvironment.systemEnvironment()
        environment.insert("LC_ALL", "C")
        self.process.setProcessEnvironment(environment)
        self.process.finished.connect(self.finish)
        self.process.errorOccurred.connect(self.error)
        self.timeout = QTimer(self)
        self.timeout.setSingleShot(True)
        self.timeout.timeout.connect(self.process.kill)
        self.busy = False

    def start(self, program, arguments):
        if self.busy:
            return False
        self.busy = True
        self.process.start(program, arguments)
        self.timeout.start(1500)
        return True

    def error(self, error):
        if error == QProcess.FailedToStart and self.busy:
            self.busy = False
            self.timeout.stop()
            self.completed.emit(-1, "", self.process.errorString())

    def finish(self, code, status):
        if not self.busy:
            return
        self.busy = False
        self.timeout.stop()
        output = bytes(self.process.readAllStandardOutput()).decode(errors="replace")
        error = bytes(self.process.readAllStandardError()).decode(errors="replace")
        self.completed.emit(code if status == QProcess.NormalExit else -1, output, error)

    def stop(self):
        self.timeout.stop()
        self.busy = False
        if self.process.state() != QProcess.NotRunning:
            self.process.kill()
            self.process.waitForFinished(500)
