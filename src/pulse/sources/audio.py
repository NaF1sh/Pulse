"""Read-only PipeWire default-output volume sampling."""
import re
import shutil

from PySide6.QtCore import QObject, QTimer, Signal

from pulse.core.models import Kind, Notification
from pulse.sources.command import Command


def parse_volume(output):
    match = re.fullmatch(r"Volume:\s+(\d+(?:\.\d+)?)\s*(\[MUTED\])?\s*", output.strip())
    if not match:
        raise ValueError("Unexpected wpctl volume output")
    value = float(match[1])
    if not 0 <= value <= 10:
        raise ValueError("Volume outside supported range")
    return round(value, 2), bool(match[2])


class Audio(QObject):
    notification = Signal(object)
    status = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.command = Command(self)
        self.command.completed.connect(self.received)
        self.timer = QTimer(self)
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.poll)
        self.previous = None
        self.last_error = ""
        self.executable = None

    def start(self):
        self.executable = shutil.which("wpctl")
        if not self.executable:
            self.status.emit("Volume source unavailable: wpctl is not installed.")
            return
        self.timer.start()
        self.poll()

    def poll(self):
        self.command.start(self.executable, ["get-volume", "@DEFAULT_AUDIO_SINK@"])

    def received(self, code, output, error):
        try:
            if code != 0:
                raise ValueError("Cannot read PipeWire volume; check your audio session.")
            state = parse_volume(output)
        except ValueError as failure:
            if str(failure) != self.last_error:
                self.status.emit(f"Volume source: {failure}")
            self.last_error = str(failure)
            self.timer.setInterval(5000)
            self.previous = None
            return
        if self.previous is None:
            self.status.emit("Volume source ready; watching output changes.")
        changed = self.previous is not None and state != self.previous
        self.previous = state
        self.last_error = ""
        self.timer.setInterval(500)
        if changed:
            value, muted = state
            self.notification.emit(Notification(
                -2000002, "Audio", "Muted" if muted else "Volume", "Default output",
                timeout=2.5, kind=Kind.LEVEL, value=0 if muted else min(value, 1),
                value_label="Muted" if muted else f"{round(value * 100)}%"))

    def stop(self):
        self.timer.stop()
        self.command.stop()
