import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
from PySide6.QtCore import QCoreApplication

from pulse.core.models import Priority
from pulse.sources.dbus_observer import NotificationDecoder, Observer, clean_text


def call(cookie=7, replaces=0, urgency=1, timeout=-1):
    return {"type": "method_call", "sender": ":1.20", "cookie": cookie,
            "path": "/org/freedesktop/Notifications",
            "interface": "org.freedesktop.Notifications", "member": "Notify",
            "payload": {"type": "susssasa{sv}i", "data": [
                "Chat", replaces, "", "<b>Hello</b>", "One<br>two &amp; three",
                [], {"urgency": {"type": "y", "data": urgency}}, timeout]}}


def reply(cookie=7, server_id=42):
    return {"type": "method_return", "destination": ":1.20", "reply_cookie": cookie,
            "payload": {"type": "u", "data": [server_id]}}


def test_notification_text_urgency_and_expiry():
    item = NotificationDecoder().decode(call(urgency=2))
    assert item.title == "Hello"
    assert item.body == "One two & three"
    assert item.priority == Priority.HIGH
    assert item.timeout == 0
    assert NotificationDecoder().decode(call(timeout=2500)).timeout == 2.5
    assert NotificationDecoder().decode(call(timeout=0)).timeout == 0


def test_replies_correlate_replacements_and_close_events():
    decoder = NotificationDecoder()
    first = decoder.decode(call())
    assert decoder.decode(reply()) is None
    updated = decoder.decode(call(cookie=8, replaces=42))
    assert first.id == updated.id
    decoder.decode(reply(cookie=8))
    closed = decoder.decode({"type": "signal", "interface": "org.freedesktop.Notifications",
                             "member": "NotificationClosed",
                             "payload": {"type": "uu", "data": [42, 2]}})
    assert closed == first.id
    assert 42 not in decoder.server_ids


def test_same_serial_from_different_clients_does_not_collide():
    decoder = NotificationDecoder()
    first = decoder.decode(call())
    other = call()
    other["sender"] = ":1.21"
    second = decoder.decode(other)
    decoder.decode(reply())
    other_reply = reply(server_id=43)
    other_reply["destination"] = ":1.21"
    decoder.decode(other_reply)
    assert decoder.server_ids == {42: first.id, 43: second.id}


@pytest.mark.parametrize("message", [None, [], {}, {"payload": None},
    {"type": "method_return", "payload": {"data": None}},
    {"type": "method_call", "member": "Other"}])
def test_unrelated_and_malformed_messages_are_ignored(message):
    assert NotificationDecoder().decode(message) is None


def test_huge_body_and_missing_fields_are_safe():
    message = call()
    message["payload"]["data"][0] = None
    message["payload"]["data"][3] = ""
    message["payload"]["data"][4] = "x" * 10000
    item = NotificationDecoder().decode(message)
    assert item.app == "Application"
    assert item.title == "Notification"
    assert len(item.body) == 600


def test_monitor_handles_fragmented_json_and_multiple_lines():
    app = QCoreApplication.instance() or QCoreApplication([])
    observer = Observer()
    notifications = []
    observer.notification.connect(notifications.append)
    wire = (json.dumps(call()) + "\n" + json.dumps(reply()) + "\n").encode()

    class Stream:
        chunk = b""
        def readAllStandardOutput(self):
            return self.chunk

    stream = Stream()
    observer.process = stream
    stream.chunk = wire[:30]
    observer.read_output()
    assert notifications == []
    stream.chunk = wire[30:]
    observer.read_output()
    assert len(notifications) == 1
    assert observer.decoder.server_ids[42] == notifications[0].id
    assert observer.buffer == b""


def test_unavailable_bus_stays_open_with_clear_error():
    root = Path(__file__).resolve().parents[1]
    env = dict(os.environ, PYTHONPATH=str(root / "src"),
               DBUS_SESSION_BUS_ADDRESS="unix:path=/tmp/pulse-nonexistent-test-bus")
    result = subprocess.run([sys.executable, "-m", "pulse.main", "--backend", "offscreen",
                             "--observe", "--no-history", "--quit-after", "3"],
                            env=env, capture_output=True, text=True, timeout=10)
    assert result.returncode == 0
    assert "Pulse observer unavailable:" in result.stderr
    assert "QProcess: Destroyed" not in result.stderr


def test_action_and_desktop_metadata_are_preserved_and_sanitized():
    message = call()
    message['payload']['data'][5] = ['default', 'Open', 'mark', '<b>Mark read</b>',
                                      'mark', 'Duplicate', 'inline-reply', 'Reply']
    message['payload']['data'][6]['desktop-entry'] = {'type': 's', 'data': 'discord'}
    item = NotificationDecoder().decode(message)
    assert item.actions == (('default', 'Open'), ('mark', 'Mark read'))
    assert item.desktop_entry == 'discord'


@pytest.mark.parametrize('actions', [None, ['odd'], ['key', 1], 'bad'])
def test_malformed_actions_do_not_break_notification(actions):
    message = call()
    message['payload']['data'][5] = actions
    assert NotificationDecoder().decode(message).actions == ()


def test_notification_monitor_retries_after_connection_failure():
    root = Path(__file__).resolve().parents[1]
    env = dict(os.environ, PYTHONPATH=str(root / 'src'),
               DBUS_SESSION_BUS_ADDRESS='unix:path=/tmp/pulse-nonexistent-retry-bus')
    result = subprocess.run([sys.executable, '-m', 'pulse.main', '--backend', 'offscreen',
                             '--observe', '--no-history', '--no-music', '--no-volume',
                             '--quit-after', '17'], env=env, capture_output=True, text=True, timeout=25)
    assert result.returncode == 0, result.stderr
    assert result.stderr.count('Pulse observer unavailable:') >= 2
    assert 'QProcess: Destroyed' not in result.stderr


def test_monitor_failure_revokes_readiness_and_restart_clears_ids(monkeypatch):
    from PySide6.QtCore import QProcess
    observer = Observer()
    readiness = []
    observer.readinessChanged.connect(readiness.append)
    observer.set_ready(True)
    observer.failed.emit('Disconnected')
    assert readiness == [True, False]
    observer.decoder.server_ids[5] = 7
    monkeypatch.setattr('pulse.sources.dbus_observer.shutil.which', lambda _: None)
    observer.start()
    assert observer.decoder.server_ids == {}
    assert observer.monitor_ready is False
