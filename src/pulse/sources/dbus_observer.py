"""Read-only notification adapter using busctl's JSON monitor output."""
from collections import OrderedDict
from html.parser import HTMLParser
import json
import shutil

from PySide6.QtCore import QObject, QProcess, Signal

from pulse.core.models import Notification, Priority


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

    def handle_starttag(self, tag, attrs):
        if tag in {"br", "p", "div"}:
            self.parts.append(" ")


def clean_text(value, limit):
    if not isinstance(value, str):
        return ""
    parser = PlainText()
    parser.feed(value[:limit * 4])
    return " ".join("".join(parser.parts).split())[:limit]


class NotificationDecoder:
    """Correlate Notify replies with server IDs without replying to any call."""
    def __init__(self, default_timeout=5.0):
        self.next_id = 1
        self.default_timeout = default_timeout
        self.calls = OrderedDict()
        self.server_ids = OrderedDict()

    def decode(self, message):
        if not isinstance(message, dict):
            return None
        payload = message.get("payload", {})
        if not isinstance(payload, dict):
            return None
        data = payload.get("data", [])
        if not isinstance(data, list):
            return None
        if (message.get("type") == "signal"
                and message.get("interface") == "org.freedesktop.Notifications"
                and message.get("member") == "NotificationClosed"
                and payload.get("type") == "uu" and len(data) == 2
                and type(data[0]) is int):
            return self.server_ids.pop(data[0], None)
        if message.get("type") == "method_return":
            key = (message.get("destination"), message.get("reply_cookie"))
            local_id = self.calls.pop(key, None)
            if (local_id is not None and payload.get("type") == "u" and len(data) == 1
                    and type(data[0]) is int and data[0] > 0):
                self.server_ids[data[0]] = local_id
                if len(self.server_ids) > 1024:
                    self.server_ids.popitem(last=False)
            return None
        if (message.get("type") != "method_call"
                or message.get("path") != "/org/freedesktop/Notifications"
                or message.get("interface") != "org.freedesktop.Notifications"
                or message.get("member") != "Notify"
                or payload.get("type") != "susssasa{sv}i"
                or not isinstance(data, list) or len(data) != 8):
            return None
        app, replaces_id, icon, title, body, actions, hints, timeout = data
        if (type(replaces_id) is not int or replaces_id < 0
                or type(timeout) is not int or not isinstance(hints, dict)):
            return None
        local_id = self.server_ids.get(replaces_id) if replaces_id else None
        if local_id is None:
            local_id = self.next_id
            self.next_id += 1
        key = (message.get("sender"), message.get("cookie"))
        self.calls[key] = local_id
        if len(self.calls) > 1024:
            self.calls.popitem(last=False)
        urgency = hints.get("urgency", {})
        urgency = urgency.get("data", 1) if isinstance(urgency, dict) else 1
        priority = Priority(urgency) if type(urgency) is int and urgency in (0, 1, 2) else Priority.NORMAL
        seconds = 0 if timeout == 0 else (self.default_timeout if timeout < 0 else min(timeout / 1000, 3600))
        if priority == Priority.HIGH and timeout < 0:
            seconds = 0
        entry_hint = hints.get("desktop-entry", {})
        desktop_entry = entry_hint.get("data", "") if isinstance(entry_hint, dict) else ""
        if not isinstance(desktop_entry, str) or len(desktop_entry) > 256:
            desktop_entry = ""
        parsed_actions = []
        if (isinstance(actions, list) and len(actions) % 2 == 0
                and all(isinstance(value, str) for value in actions)):
            seen = set()
            for action_key, label in zip(actions[::2], actions[1::2]):
                if (not action_key or len(action_key) > 256 or action_key in seen
                        or action_key == "inline-reply"):
                    continue
                seen.add(action_key)
                parsed_actions.append((action_key, clean_text(label, 60) or "Open"))
                if len(parsed_actions) == 8:
                    break
        return Notification(local_id, clean_text(app, 80) or "Application",
                            clean_text(title, 160) or "Notification",
                            clean_text(body, 600), priority, seconds,
                            desktop_entry=desktop_entry, actions=tuple(parsed_actions))


class Observer(QObject):
    notification = Signal(object)
    closed = Signal(int)
    metadataChanged = Signal()
    status = Signal(str)
    failed = Signal(str)

    def __init__(self, parent=None, *, default_timeout=5.0):
        super().__init__(parent)
        self.decoder = NotificationDecoder(default_timeout)
        self.buffer = bytearray()
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.readyReadStandardError.connect(self.read_error)
        self.process.errorOccurred.connect(lambda _: self.failed.emit(self.process.errorString()))
        self.process.finished.connect(self.finished)
        self.stopping = False
        self.error = ""
        self.received = False

    def start(self):
        executable = shutil.which("busctl")
        if executable is None:
            self.failed.emit("busctl is required for observer mode (install systemd tools).")
            return
        self.status.emit("Starting read-only notification monitor…")
        self.process.start(executable, ["--user", "--json=short", "--no-pager",
                                        "monitor", "org.freedesktop.Notifications"])

    def read_output(self):
        self.buffer.extend(bytes(self.process.readAllStandardOutput()))
        while b"\n" in self.buffer:
            line, _, remainder = self.buffer.partition(b"\n")
            self.buffer = bytearray(remainder)
            if not line.strip():
                continue
            try:
                message = json.loads(line)
                item = self.decoder.decode(message)
                if isinstance(message, dict) and message.get("type") == "method_return":
                    self.metadataChanged.emit()
            except (ValueError, TypeError, KeyError, IndexError, RecursionError):
                continue
            if not self.received:
                self.received = True
                self.status.emit("Observer receiving; Plasma still handles notifications.")
            if type(item) is int:
                self.closed.emit(item)
            elif item is not None:
                self.notification.emit(item)
        if len(self.buffer) > 2 * 1024 * 1024:
            self.failed.emit("Notification monitor exceeded the message-size limit.")
            self.stop()

    def read_error(self):
        text = bytes(self.process.readAllStandardError()).decode(errors="replace").strip()
        self.error = (self.error + " " + text)[-2000:]
        if "Monitoring bus message stream" in text:
            self.status.emit("Observer ready; Plasma still handles notifications.")

    def finished(self, code, exit_status):
        if not self.stopping:
            self.failed.emit(self.error.strip() or f"Notification monitor exited ({code}).")

    def stop(self):
        self.stopping = True
        if self.process.state() != QProcess.NotRunning:
            self.process.terminate()
            if not self.process.waitForFinished(1000):
                self.process.kill()
                self.process.waitForFinished(1000)
