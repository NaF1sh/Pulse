import subprocess
from types import SimpleNamespace

from pulse.diagnostics import checks


def test_missing_optional_tools_are_reported_without_failure(monkeypatch):
    monkeypatch.setattr('pulse.diagnostics.shutil.which', lambda _: None)
    monkeypatch.delenv('DISPLAY', raising=False)
    monkeypatch.delenv('WAYLAND_DISPLAY', raising=False)
    rows = {item['name']: item for item in checks()}
    assert rows['Display']['state'] == 'warning'
    assert rows['Notifications and music']['state'] == 'warning'
    assert rows['Volume feedback']['state'] == 'warning'


def test_notification_service_and_bus_timeout(monkeypatch):
    monkeypatch.setattr('pulse.diagnostics.shutil.which', lambda name: '/usr/bin/' + name)
    monkeypatch.setattr('pulse.diagnostics.subprocess.run', lambda *a, **k:
                        SimpleNamespace(returncode=0, stdout='org.freedesktop.Notifications 123 plasma user\n'))
    assert next(row for row in checks() if row['name'] == 'Notification service')['state'] == 'ok'
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired('busctl', 3)
    monkeypatch.setattr('pulse.diagnostics.subprocess.run', timeout)
    assert next(row for row in checks() if row['name'] == 'Session bus')['state'] == 'warning'
